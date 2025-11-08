from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from api_connector import APIConnector
from balance_monitor import BalanceMonitor
from data_access import (
    PaymentScheduleRepository,
    RiskAssessmentRepository,
    User,
    UserRepository,
)
from model_loader import BaseArcLLM, ModelLoader
from notification_service import NotificationService
from schedule_utils import next_run

logger = logging.getLogger(__name__)


@dataclass
class GuardianDecision:
    decision: str
    risk_score: float
    payment_id: Optional[str]
    reason: str

    def to_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "riskScore": self.risk_score,
            "paymentId": self.payment_id,
            "reason": self.reason,
        }


class GuardianAgent:
    def __init__(self, model_loader: Optional[ModelLoader] = None) -> None:
        self.llm: BaseArcLLM = (model_loader or ModelLoader()).get()
        self.api = APIConnector()
        self.notifier = NotificationService()
        self.balance_monitor = BalanceMonitor(self.api, self.notifier)
        self.users = UserRepository()
        self.payments = PaymentScheduleRepository()
        self.risk_repo = RiskAssessmentRepository()

    def _resolve_user(self, user_id: str) -> User:
        user = self.users.get_user(user_id)
        if not user:
            raise ValueError(f"Unknown user {user_id}")
        return user

    def _resolve_recipient(self, user: User, entities: Dict[str, Any]) -> Dict[str, Any]:
        recipient_id = entities.get("recipientId")
        for recipient in user.whitelisted_recipients:
            if recipient["recipientId"] == recipient_id:
                return recipient
        return {
            "recipientId": recipient_id or "unknown",
            "name": entities.get("recipientName", "Unknown recipient"),
            "address": entities.get("recipientAddress", ""),
            "currency": entities.get("currency", "USDC"),
        }

    def _verify_recipient(self, recipient: Dict[str, Any]) -> Dict[str, Any]:
        if not recipient.get("address"):
            return {"status": "unknown", "details": "No address provided"}
        result = self.api.verify_recipient(recipient["address"])
        if result.success:
            return {"status": "verified", "details": result.payload}
        return {"status": "unverified", "details": result.error}

    def _determine_amount(self, entities: Dict[str, Any]) -> float:
        amount = entities.get("amount")
        if amount is None:
            raise ValueError("Payment amount missing")
        return float(amount)

    def _calculate_features(self, user: User, entities: Dict[str, Any], amount: float, is_new_recipient: bool, balance: float) -> Dict[str, Any]:
        preferences = user.preferences
        max_amount = float(preferences.get("maxPaymentAmount", 0) or amount)
        schedule = entities.get("schedule", {})
        frequency = schedule.get("frequency", "once")
        freq_weight = 1 if frequency == "once" else 3 if frequency == "daily" else 2
        balance_ratio = (balance / amount) if amount else 1
        return {
            "amount": amount,
            "max_amount": max_amount,
            "frequency": freq_weight,
            "new_recipient": is_new_recipient,
            "balance_ratio": balance_ratio,
        }

    def _schedule_payment(self, user: User, entities: Dict[str, Any], amount: float, currency: str) -> Dict[str, Any]:
        payment_id = entities.get("paymentId") or f"pay-{uuid.uuid4().hex[:8]}"
        scheduled_at = entities.get("scheduledTimestamp")
        schedule = entities.get("schedule", {})
        if not scheduled_at:
            if schedule:
                scheduled_at = next_run(schedule) or (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
            else:
                scheduled_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        payment = {
            "paymentId": payment_id,
            "userId": user.userId,
            "recipient": entities.get("recipientId"),
            "amount": amount,
            "currency": currency,
            "conditions": schedule,
            "status": "APPROVED",
            "scheduledTimestamp": scheduled_at,
        }
        self.payments.upsert(payment)
        return payment

    def _record_assessment(self, request_payload: Dict[str, Any], features: Dict[str, Any], model_output: Dict[str, Any], verification: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "request": request_payload,
            "features": features,
            "model": model_output,
            "verification": verification,
        }
        self.risk_repo.append(record)
        return record

    def process(self, payload: Dict[str, Any]) -> GuardianDecision:
        user_id = payload.get("userId")
        entities = payload.get("entities", {})
        if payload.get("intent") == "analyze_transactions":
            analysis_request = entities.get("analysisRequest", {})
            transactions = analysis_request.get("transactions", [])
            count = analysis_request.get("count", len(transactions) or 2)
            result = self.analyze_transactions(user_id, transactions, payload.get("rawText", ""), count)
            return GuardianDecision(
                decision="ANALYSIS",
                risk_score=0.0,
                payment_id=None,
                reason=result["summary"],
            )
        if not user_id:
            raise ValueError("userId is required")
        user = self._resolve_user(user_id)
        recipient = self._resolve_recipient(user, entities)
        verification = self._verify_recipient(recipient)
        is_new_recipient = recipient["recipientId"] not in [r["recipientId"] for r in user.whitelisted_recipients]
        amount = self._determine_amount(entities)
        currency = entities.get("currency", recipient.get("currency", "USDC"))
        balance_result = self.balance_monitor.fetch_balance(user.data)
        balance = balance_result.payload.get("balance", 0) if balance_result and balance_result.success else 0
        features = self._calculate_features(user, entities, amount, is_new_recipient, balance)
        decision_context = {
            "userId": user.userId,
            "recipient": recipient,
            "amount": amount,
            "currency": currency,
            "balance": balance,
            "features": features,
        }
        model_output = self.llm.score_risk(decision_context)
        self._record_assessment(payload, features, model_output, verification)
        decision = model_output.get("decision", "FLAG_FOR_REVIEW")
        payment_id: Optional[str] = None
        reason = ""
        confirmed = bool(
            entities.get("confirmation")
            or entities.get("confirmed")
            or entities.get("confirm")
        )
        if not confirmed:
            reason = (
                f"Confirm payment of {amount} {currency} to {recipient.get('name')} "
                f"(id {recipient.get('recipientId')})."
            )
            return GuardianDecision(
                decision="AWAITING_CONFIRMATION",
                risk_score=model_output.get("riskScore", 0.0),
                payment_id=None,
                reason=reason,
            )

        if decision == "APPROVE":
            if balance < amount:
                decision = "DENY"
                reason = "Insufficient balance at approval time"
            else:
                scheduled = self._schedule_payment(user, entities, amount, currency)
                payment_id = scheduled["paymentId"]
                reason = "Payment scheduled"
        elif decision == "FLAG_FOR_REVIEW":
            reason = "Manual review required"
            self.notifier.notify_admin("Payment flagged", f"Payload: {payload}")
        else:
            reason = "Risk too high"

        logger.info(
            "Guardian decision %s (risk %.2f) for user %s",
            decision,
            model_output.get("riskScore", 0.0),
            user_id,
        )
        return GuardianDecision(
            decision=decision,
            risk_score=model_output.get("riskScore", 0.0),
            payment_id=payment_id,
            reason=reason,
        )

    def analyze_transactions(self, user_id: str, transactions: List[Dict[str, Any]], question: str, count: int) -> Dict[str, Any]:
        if not user_id:
            raise ValueError("userId is required for analysis")
        if not transactions:
            return {"summary": "No executed transactions available to analyze."}
        facts = []
        for tx in transactions[:count]:
            facts.append(
                (
                    f"Payment {tx.get('paymentId')} -> {tx.get('recipient')} executed "
                    f"for {tx.get('amount')} {tx.get('currency')} on {tx.get('lastExecutedAt') or tx.get('updatedAt')}"
                )
            )
        summary = self.llm.answer_question(question or "Analyze past transactions.", facts)
        return {"summary": summary, "transactions": facts}


__all__ = ["GuardianAgent", "GuardianDecision"]
