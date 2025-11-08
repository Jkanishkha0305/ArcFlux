from __future__ import annotations

import copy
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from data_access import StockRepository

logger = logging.getLogger(__name__)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class StockSelectionAgent:
    """Curates stock options before routing the purchase to the Guardian agent."""

    def __init__(self, repository: Optional[StockRepository] = None) -> None:
        self.repo = repository or StockRepository()

    def process(self, intent_payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = copy.deepcopy(intent_payload)
        entities = payload.setdefault("entities", {})
        request = entities.get("stockRequest", {}) or {}
        amount = entities.get("amount")
        if amount is not None:
            request["budget"] = _safe_float(amount, 0.0)
        entities["stockRequest"] = request
        selection = self._extract_selection(entities)

        if not selection:
            recommendations = self._build_recommendations(request)
            if not recommendations:
                return {
                    "status": "NO_MATCHES",
                    "message": "No stocks matched the provided filters. Try another sector or criteria.",
                }
            prompt = self._build_prompt(request, recommendations)
            return {
                "status": "AWAITING_SELECTION",
                "prompt": prompt,
                "recommendations": recommendations,
            }

        stock = self.repo.find(selection)
        if not stock:
            return {
                "status": "INVALID_SELECTION",
                "message": f"Symbol '{selection}' was not found. Reply with one of the suggested symbols.",
            }

        prepared_payload = self._attach_selection(payload, stock, request)
        logger.info("Stock selection %s prepared for guardian routing", stock["symbol"])
        return {
            "status": "READY_FOR_GUARDIAN",
            "selection": {
                "symbol": stock["symbol"],
                "name": stock["name"],
                "sector": stock["sector"],
                "price": stock["price"],
            },
            "message": f"Selected {stock['symbol']} ({stock['name']}). Passing to Guardian for risk review.",
            "payload": prepared_payload,
        }

    def _build_recommendations(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        sector = request.get("sector")
        records = self.repo.list_by_sector(sector)
        if not records:
            records = self.repo.list_all()
        budget = _safe_float(request.get("budget"))
        recommendations: List[Dict[str, Any]] = []
        for record in records:
            score, discount_pct = self._score_stock(record, budget)
            recommendations.append(
                {
                    "symbol": record.get("symbol"),
                    "name": record.get("name"),
                    "sector": record.get("sector"),
                    "price": record.get("price"),
                    "peRatio": record.get("peRatio"),
                    "dividendYield": record.get("dividendYield"),
                    "discountToPeersPct": discount_pct,
                    "valuationScore": score,
                    "memo": (
                        f"{record.get('symbol')} trades {discount_pct:.1f}% below peer price with "
                        f"P/E {record.get('peRatio')} vs peer {record.get('peerAveragePe')}"
                    ),
                }
            )
        recommendations.sort(key=lambda item: item["valuationScore"], reverse=True)
        return recommendations[:3]

    def _score_stock(self, record: Dict[str, Any], budget: float) -> Tuple[float, float]:
        peer_price = _safe_float(record.get("peerAveragePrice"), record.get("price", 1))
        price = _safe_float(record.get("price"), peer_price)
        discount = max(0.0, peer_price - price)
        discount_pct = (discount / peer_price * 100) if peer_price else 0.0

        peer_pe = _safe_float(record.get("peerAveragePe"), record.get("peRatio", 1))
        pe_ratio = _safe_float(record.get("peRatio"), peer_pe)
        pe_edge = max(0.0, peer_pe - pe_ratio)
        pe_edge_pct = (pe_edge / peer_pe) if peer_pe else 0.0

        yield_score = min(_safe_float(record.get("dividendYield")), 0.05) / 0.05
        affordability = 1.0 if not budget else min(1.0, budget / price) if price else 0.0

        raw_score = (discount_pct * 0.4) + (pe_edge_pct * 100 * 0.3) + (yield_score * 20 * 0.15) + (affordability * 20 * 0.15)
        normalized = round(raw_score / 100, 3)
        return normalized, round(discount_pct, 1)

    def _build_prompt(self, request: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
        sector = (request.get("sector") or "mixed").lower()
        names = ", ".join(f"{rec['symbol']} ({rec['price']} USDC)" for rec in recommendations)
        return (
            f"I found these {sector} stocks reasonably valued versus peers: {names}. "
            "Reply with a symbol to proceed."
        )

    def _extract_selection(self, entities: Dict[str, Any]) -> Optional[str]:
        explicit = entities.get("selectedStock") or entities.get("selectedSymbol")
        if isinstance(explicit, str) and explicit.strip():
            return explicit.strip().upper()
        selected = entities.get("stockSelection", {})
        if isinstance(selected, dict):
            symbol = selected.get("symbol")
            if symbol:
                return str(symbol).upper()
            symbols = selected.get("symbols")
            if isinstance(symbols, list) and symbols:
                return str(symbols[0]).upper()
        manual_list = entities.get("selectedStocks")
        if isinstance(manual_list, list) and manual_list:
            return str(manual_list[0]).upper()
        text = entities.get("rawText") or ""
        inferred = self._infer_symbol_from_text(text)
        return inferred

    def _infer_symbol_from_text(self, text: str) -> Optional[str]:
        if not text:
            return None
        tokens = re.findall(r"[A-Za-z]{3,5}", text.upper())
        seen: set[str] = set()
        for token in tokens:
            if token in seen:
                continue
            seen.add(token)
            record = self.repo.find(token)
            if record:
                return token
        lowered = text.lower()
        for record in self.repo.list_all():
            name = str(record.get("name", "")).lower()
            if name and name in lowered:
                return record.get("symbol")
        return None

    def _attach_selection(self, payload: Dict[str, Any], stock: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        entities = payload.setdefault("entities", {})
        budget = _safe_float(request.get("budget")) or _safe_float(entities.get("amount")) or _safe_float(stock.get("price"))
        if budget <= 0:
            budget = _safe_float(stock.get("price"))
        entities["amount"] = round(budget, 2)
        entities.setdefault("currency", "USDC")
        entities["recipientId"] = f"stock::{stock.get('symbol')}"
        entities["recipientName"] = f"{stock.get('name')} ({stock.get('symbol')})"
        entities["recipientAddress"] = f"arc1stock{stock.get('symbol', '').lower()}"
        entities.setdefault("memo", f"Stock purchase for {stock.get('symbol')}")
        entities["stockSelection"] = {
            "symbol": stock.get("symbol"),
            "price": stock.get("price"),
            "sector": stock.get("sector"),
            "budget": entities["amount"],
        }
        entities.setdefault("confirmation", True)
        return payload


__all__ = ["StockSelectionAgent"]
