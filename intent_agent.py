from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from data_access import User, UserRepository
from model_loader import BaseArcLLM, ModelLoader

logger = logging.getLogger(__name__)


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
        if intent in {"make_payment", "schedule_payment", "settings"}:
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
        user = self.user_repo.get_user(user_id)
        if user:
            self._autofill_recipient(user, text, entities)
        schedule = self._extract_schedule(text)
        if schedule:
            entities.setdefault("schedule", schedule)
        target = self._route(model_result["intent"])
        logger.info("Routed intent '%s' for user %s to %s", model_result["intent"], user_id, target)
        return IntentResult(
            user_id=user_id,
            intent=model_result["intent"],
            entities=entities,
            confidence=model_result["confidence"],
            target_agent=target,
            raw_text=text,
        )


__all__ = ["IntentAgent", "IntentResult"]
