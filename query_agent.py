from __future__ import annotations

import logging
from typing import Dict, List, Optional

from balance_monitor import BalanceMonitor
from data_access import PaymentScheduleRepository, RiskAssessmentRepository, UserRepository
from model_loader import BaseArcLLM, ModelLoader

logger = logging.getLogger(__name__)


class QueryAgent:
    def __init__(self, model_loader: Optional[ModelLoader] = None) -> None:
        self.llm: BaseArcLLM = (model_loader or ModelLoader()).get()
        self.users = UserRepository()
        self.payments = PaymentScheduleRepository()
        self.risk_repo = RiskAssessmentRepository()
        self.balance_monitor = BalanceMonitor()

    def _format_payment(self, record: Dict[str, any]) -> str:
        return (
            f"Payment {record.get('paymentId')} to {record.get('recipient')} "
            f"for {record.get('amount')} {record.get('currency')} is {record.get('status')} "
            f"on {record.get('scheduledTimestamp')}"
        )

    def _fetch_upcoming(self, user_id: str) -> List[str]:
        upcoming = [p for p in self.payments.list(user_id) if p.get("status") in {"APPROVED", "SCHEDULED"}]
        upcoming.sort(key=lambda p: p.get("scheduledTimestamp"))
        return [self._format_payment(p) for p in upcoming[:5]]

    def _fetch_history(self, user_id: str) -> List[str]:
        history = [p for p in self.payments.list(user_id) if p.get("status") == "EXECUTED"]
        history.sort(key=lambda p: p.get("updatedAt", ""), reverse=True)
        return [self._format_payment(p) for p in history[:5]]

    def _fetch_risk_flags(self, user_id: str) -> List[str]:
        items = [r for r in self.risk_repo.list() if r.get("request", {}).get("userId") == user_id]
        flagged = [r for r in items if r.get("model", {}).get("decision") == "FLAG_FOR_REVIEW"]
        return [f"Request on {r.get('timestamp')} flagged with risk {r.get('model', {}).get('riskScore')}" for r in flagged]

    def _fetch_balance(self, user_id: str) -> List[str]:
        user = self.users.get_user(user_id)
        if not user:
            return ["User record missing"]
        result = self.balance_monitor.fetch_balance(user.data)
        if not result:
            return ["Balance service unavailable"]
        if result.success:
            return [
                f"Current balance: {result.payload.get('balance')} {result.payload.get('currency')}"
            ]
        return [f"Balance check failed: {result.error}"]

    def _determine_topic(self, question: str) -> str:
        lowered = question.lower()
        if any(word in lowered for word in ["upcoming", "next", "scheduled"]):
            return "upcoming"
        if any(word in lowered for word in ["executed", "history", "past"]):
            return "history"
        if "risk" in lowered or "flag" in lowered:
            return "risk"
        if "balance" in lowered:
            return "balance"
        return "upcoming"

    def answer(self, user_id: str, question: str) -> str:
        topic = self._determine_topic(question)
        if topic == "upcoming":
            facts = self._fetch_upcoming(user_id)
        elif topic == "history":
            facts = self._fetch_history(user_id)
        elif topic == "risk":
            facts = self._fetch_risk_flags(user_id)
        else:
            facts = self._fetch_balance(user_id)
        logger.info("QueryAgent answering topic %s for user %s", topic, user_id)
        return self.llm.answer_question(question, facts)


__all__ = ["QueryAgent"]
