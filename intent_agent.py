from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from data_access import PaymentScheduleRepository, StockRepository, User, UserRepository
from model_loader import BaseArcLLM, ModelLoader

logger = logging.getLogger(__name__)

STOCK_KEYWORDS = ("stock", "stocks", "equity", "equities", "share", "shares")
VALUE_KEYWORDS = ("value", "undervalued", "discount", "cheap", "least value")
SECTOR_KEYWORDS = {
    "banking": ("bank", "banking", "financial", "fintech"),
    "technology": ("technology", "tech", "software", "platform"),
    "energy": ("energy", "renewable", "solar", "power"),
    "industrial": ("industrial", "manufacturing", "supply", "logistics"),
}


@dataclass
class IntentResult:
    user_id: str
    intent: str
    entities: Dict[str, Any]
    confidence: float
    target_agent: str
    raw_text: str

    def to_payload(self) -> Dict[str, Any]:
        return {
            "userId": self.user_id,
            "intent": self.intent,
            "entities": self.entities,
            "confidence": self.confidence,
            "targetAgent": self.target_agent,
            "rawText": self.raw_text,
        }


class IntentAgent:
    def __init__(self, model_loader: Optional[ModelLoader] = None) -> None:
        self.llm: BaseArcLLM = (model_loader or ModelLoader()).get()
        self.user_repo = UserRepository()
        self.stock_repo = StockRepository()
        self.payments = PaymentScheduleRepository()

    def _transcribe_audio(self, audio_b64: str) -> str:
        try:
            audio_bytes = base64.b64decode(audio_b64)
            logger.debug("Decoded %d bytes of audio", len(audio_bytes))
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to decode audio input: %s", exc)
            return ""
        # Placeholder transcription step
        return ""  # In a real system we would pass audio_bytes to ElevenLabs/Whisper

    def _route(self, intent: str) -> str:
        if intent == "stock_purchase":
            return "stock"
        if intent in {"make_payment", "schedule_payment", "settings", "analyze_transactions"}:
            return "guardian"
        return "query"

    def _autofill_recipient(self, user: User, text: str, entities: Dict[str, Any]) -> None:
        lowered = text.lower()
        for recipient in user.whitelisted_recipients:
            recipient_id = recipient.get("recipientId", "").lower()
            recipient_name = recipient.get("name", "").lower()
            if recipient_id and recipient_id in lowered or recipient_name and recipient_name in lowered:
                entities.setdefault("recipientId", recipient.get("recipientId"))
                entities.setdefault("recipientName", recipient.get("name"))
                entities.setdefault("recipientAddress", recipient.get("address"))
                entities.setdefault("currency", recipient.get("currency", "USDC"))
                break

    def _extract_schedule(self, text: str) -> Optional[Dict[str, Any]]:
        lowered = text.lower()
        interval_match = re.search(r"every\s+(\d+)\s*(second|sec|s|minute|min|hour|day)s?", lowered)
        if interval_match:
            value = int(interval_match.group(1))
            unit = interval_match.group(2)
            multipliers = {
                "second": 1,
                "sec": 1,
                "s": 1,
                "minute": 60,
                "min": 60,
                "hour": 3600,
                "day": 86400,
            }
            seconds = value * multipliers.get(unit, 1)
            return {
                "recurring": True,
                "frequency": "interval",
                "intervalSeconds": seconds,
            }
        monthly_match = re.search(r"(?:every|each)\s+(?:month|monthly)\s*(?:on)?\s*(?:the\s*)?(\d{1,2})", lowered)
        if monthly_match:
            day = int(monthly_match.group(1))
            return {
                "recurring": True,
                "frequency": "monthly",
                "dayOfMonth": day,
            }
        return None

    def process(self, user_id: str, text: Optional[str] = None, audio_b64: Optional[str] = None) -> IntentResult:
        if not text and not audio_b64:
            raise ValueError("Either text or audio must be provided")
        if not text and audio_b64:
            text = self._transcribe_audio(audio_b64)
        if not text:
            raise ValueError("Failed to obtain textual input")

        model_result = self.llm.classify_intent(text)
        raw_entities = model_result.get("entities") or {}
        if not isinstance(raw_entities, dict):
            raw_entities = {}
        entities = {**raw_entities}
        entities.setdefault("rawText", text)
        self._ensure_amount(text, entities)
        user = self.user_repo.get_user(user_id)
        if user:
            self._autofill_recipient(user, text, entities)
        schedule = self._extract_schedule(text)
        if schedule:
            entities.setdefault("schedule", schedule)
        stock_request = self._extract_stock_request(text)
        symbol_reference = self._detect_stock_symbol(text)
        if stock_request is None and symbol_reference:
            stock_request = {}
        if symbol_reference:
            entities.setdefault("selectedStock", symbol_reference)
        analysis_request = self._extract_analysis_request(text, user_id)
        resolved_intent = model_result["intent"]
        if stock_request is not None:
            resolved_intent = "stock_purchase"
            existing_request = entities.get("stockRequest", {})
            merged_request = {**stock_request, **existing_request}
            if "budget" not in merged_request and entities.get("amount") is not None:
                merged_request["budget"] = entities["amount"]
            entities["stockRequest"] = merged_request
        if analysis_request is not None:
            resolved_intent = "analyze_transactions"
            entities["analysisRequest"] = analysis_request
        target = self._route(resolved_intent)
        logger.info("Routed intent '%s' for user %s to %s", resolved_intent, user_id, target)
        return IntentResult(
            user_id=user_id,
            intent=resolved_intent,
            entities=entities,
            confidence=model_result["confidence"],
            target_agent=target,
            raw_text=text,
        )

    def _ensure_amount(self, text: str, entities: Dict[str, Any]) -> None:
        if entities.get("amount") is not None:
            return
        match = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
        if match:
            try:
                entities["amount"] = float(match.group(1))
            except ValueError:
                logger.debug("Failed to coerce amount from %s", match.group(1))

    def _extract_stock_request(self, text: str) -> Optional[Dict[str, Any]]:
        lowered = text.lower()
        if not any(keyword in lowered for keyword in STOCK_KEYWORDS):
            return None
        sector = None
        for name, keywords in SECTOR_KEYWORDS.items():
            if any(word in lowered for word in keywords):
                sector = name.capitalize()
                break
        preference = None
        if any(word in lowered for word in VALUE_KEYWORDS):
            preference = "value"
        elif "growth" in lowered:
            preference = "growth"
        request: Dict[str, Any] = {}
        if sector:
            request["sector"] = sector
        if preference:
            request["preference"] = preference
        return request

    def _detect_stock_symbol(self, text: str) -> Optional[str]:
        tokens = re.findall(r"\b[A-Za-z]{3,5}\b", text.upper())
        for token in tokens:
            if self.stock_repo.find(token):
                return token
        return None

    def _extract_analysis_request(self, text: str, user_id: str) -> Optional[Dict[str, Any]]:
        lowered = text.lower()
        if "analy" not in lowered or "transaction" not in lowered:
            return None
        count = 2
        match = re.search(r"(\d+|one|two|three|four|five)\s+transactions?", lowered)
        if match:
            word = match.group(1)
            numbers = {
                "one": 1,
                "two": 2,
                "three": 3,
                "four": 4,
                "five": 5,
            }
            count = int(numbers.get(word, word))
        recent = self._fetch_recent_transactions(user_id, count)
        if not recent:
            return None
        return {
            "count": count,
            "transactions": recent,
        }

    def _fetch_recent_transactions(self, user_id: str, count: int) -> List[Dict[str, Any]]:
        executed = [p for p in self.payments.list(user_id) if p.get("status") == "EXECUTED"]
        executed.sort(key=lambda p: p.get("updatedAt", ""), reverse=True)
        return executed[:count]


__all__ = ["IntentAgent", "IntentResult"]
