"""
============================================
STOCK SELECTION AGENT
============================================

Curates stock options before routing the purchase to the Guardian agent.
Adapted from akb_tester branch.
"""

import copy
import re
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json
import os


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class StockRepository:
    """Repository for stock data stored in JSON file."""

    def __init__(self, data_file: Optional[str] = None):
        if data_file is None:
            # Default to stock_market_db.json in backend-python directory
            base_dir = Path(__file__).parent
            data_file = str(base_dir / "stock_market_db.json")
        self.data_file = Path(data_file)
        self._stocks: List[Dict[str, Any]] = []
        self._load_stocks()

    def _load_stocks(self):
        """Load stocks from JSON file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self._stocks = json.load(f)
            except Exception as e:
                print(f"Error loading stock data: {e}")
                self._stocks = []
        else:
            # Initialize with default stocks if file doesn't exist
            self._stocks = self._get_default_stocks()
            self._save_stocks()

    def _save_stocks(self):
        """Save stocks to JSON file."""
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self._stocks, f, indent=2)
        except Exception as e:
            print(f"Error saving stock data: {e}")

    def _get_default_stocks(self) -> List[Dict[str, Any]]:
        """Get default stock data."""
        return [
            {
                "symbol": "BNKX",
                "name": "BankX Capital",
                "sector": "Banking",
                "price": 48.72,
                "peRatio": 8.9,
                "dividendYield": 0.025,
                "peerAveragePrice": 63.15,
                "peerAveragePe": 12.1,
                "beta": 1.1,
                "esgScore": 0.62,
                "metrics": {
                    "returnOnEquity": 0.14,
                    "netMargin": 0.21,
                    "debtToEquity": 0.48
                }
            },
            {
                "symbol": "HARB",
                "name": "Harborstone Financial",
                "sector": "Banking",
                "price": 42.1,
                "peRatio": 7.5,
                "dividendYield": 0.031,
                "peerAveragePrice": 55.0,
                "peerAveragePe": 11.4,
                "beta": 0.95,
                "esgScore": 0.57,
                "metrics": {
                    "returnOnEquity": 0.16,
                    "netMargin": 0.24,
                    "debtToEquity": 0.38
                }
            },
            {
                "symbol": "CLDB",
                "name": "Cloudbridge Lending",
                "sector": "Banking",
                "price": 37.9,
                "peRatio": 6.8,
                "dividendYield": 0.018,
                "peerAveragePrice": 47.5,
                "peerAveragePe": 10.6,
                "beta": 1.05,
                "esgScore": 0.6,
                "metrics": {
                    "returnOnEquity": 0.11,
                    "netMargin": 0.18,
                    "debtToEquity": 0.52
                }
            },
            {
                "symbol": "SOLR",
                "name": "Solara Renewables",
                "sector": "Energy",
                "price": 28.45,
                "peRatio": 15.2,
                "dividendYield": 0.0,
                "peerAveragePrice": 32.0,
                "peerAveragePe": 18.7,
                "beta": 1.25,
                "esgScore": 0.81,
                "metrics": {
                    "revenueGrowth": 0.34,
                    "capacityFactor": 0.47,
                    "cashPerShare": 5.11
                }
            },
            {
                "symbol": "NEPT",
                "name": "Neptune Energy Storage",
                "sector": "Energy",
                "price": 31.05,
                "peRatio": 13.4,
                "dividendYield": 0.017,
                "peerAveragePrice": 36.2,
                "peerAveragePe": 16.9,
                "beta": 1.14,
                "esgScore": 0.77,
                "metrics": {
                    "revenueGrowth": 0.27,
                    "capacityFactor": 0.52,
                    "cashPerShare": 4.6
                }
            },
            {
                "symbol": "QNTC",
                "name": "Quantico Systems",
                "sector": "Technology",
                "price": 62.4,
                "peRatio": 19.1,
                "dividendYield": 0.0,
                "peerAveragePrice": 75.2,
                "peerAveragePe": 24.8,
                "beta": 1.32,
                "esgScore": 0.69,
                "metrics": {
                    "revenueGrowth": 0.41,
                    "grossMargin": 0.63,
                    "netCash": 1.8
                }
            },
            {
                "symbol": "STRM",
                "name": "Streamware Platforms",
                "sector": "Technology",
                "price": 54.3,
                "peRatio": 17.3,
                "dividendYield": 0.0,
                "peerAveragePrice": 66.5,
                "peerAveragePe": 22.2,
                "beta": 1.28,
                "esgScore": 0.66,
                "metrics": {
                    "revenueGrowth": 0.36,
                    "grossMargin": 0.58,
                    "netCash": 1.2
                }
            },
            {
                "symbol": "AGRX",
                "name": "AgriX Supply Chain",
                "sector": "Industrial",
                "price": 25.8,
                "peRatio": 10.4,
                "dividendYield": 0.014,
                "peerAveragePrice": 31.6,
                "peerAveragePe": 14.9,
                "beta": 0.9,
                "esgScore": 0.7,
                "metrics": {
                    "returnOnAssets": 0.09,
                    "inventoryTurns": 7.1,
                    "freeCashFlowYield": 0.085
                }
            }
        ]

    def list_all(self) -> List[Dict[str, Any]]:
        """List all stocks."""
        return self._stocks.copy()

    def list_by_sector(self, sector: Optional[str]) -> List[Dict[str, Any]]:
        """List stocks by sector."""
        if not sector:
            return self.list_all()
        wanted = sector.lower()
        return [s for s in self._stocks if s.get("sector", "").lower() == wanted]

    def find(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Find stock by symbol."""
        if not symbol:
            return None
        normalized = symbol.upper()
        for stock in self._stocks:
            if stock.get("symbol", "").upper() == normalized:
                return stock
        return None


class StockSelectionAgent:
    """Curates stock options before routing the purchase to the Guardian agent."""

    def __init__(self, repository: Optional[StockRepository] = None) -> None:
        self.repo = repository or StockRepository()

    def process(self, intent_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process stock selection request."""
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
        print(f"Stock selection {stock['symbol']} prepared for guardian routing")
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
        """Build stock recommendations based on request."""
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
        """Score a stock based on valuation metrics."""
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
        """Build prompt for user selection."""
        sector = (request.get("sector") or "mixed").lower()
        names = ", ".join(f"{rec['symbol']} ({rec['price']} USDC)" for rec in recommendations)
        return (
            f"I found these {sector} stocks reasonably valued versus peers: {names}. "
            "Reply with a symbol to proceed."
        )

    def _extract_selection(self, entities: Dict[str, Any]) -> Optional[str]:
        """Extract selected stock symbol from entities."""
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
        """Infer stock symbol from text."""
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
        """Attach stock selection to payload for guardian routing."""
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


# Global instance
stock_agent = StockSelectionAgent()

