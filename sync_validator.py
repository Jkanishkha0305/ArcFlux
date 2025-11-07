from __future__ import annotations

import logging
from typing import Dict, List

from data_access import PaymentScheduleRepository, RiskAssessmentRepository
from notification_service import NotificationService

logger = logging.getLogger(__name__)


class SyncValidator:
    def __init__(self) -> None:
        self.payments = PaymentScheduleRepository()
        self.assessments = RiskAssessmentRepository()
        self.notifier = NotificationService()

    def _index_assessments(self) -> Dict[str, List[Dict[str, any]]]:
        index: Dict[str, List[Dict[str, any]]] = {}
        for record in self.assessments.list():
            request = record.get("request", {})
            payment_id = request.get("entities", {}).get("paymentId")
            if payment_id:
                index.setdefault(payment_id, []).append(record)
        return index

    def validate(self) -> List[str]:
        issues: List[str] = []
        assessment_index = self._index_assessments()
        for payment in self.payments.list():
            payment_id = payment.get("paymentId")
            status = payment.get("status")
            records = assessment_index.get(payment_id, [])
            if status in {"APPROVED", "EXECUTED"} and not records:
                issues.append(f"Payment {payment_id} lacks risk assessment entry")
            for record in records:
                decision = record.get("model", {}).get("decision")
                if status == "EXECUTED" and decision not in {"APPROVE", "FLAG_FOR_REVIEW"}:
                    issues.append(f"Payment {payment_id} executed despite decision {decision}")
        if issues:
            body = "\n".join(issues)
            logger.error("SyncValidator detected issues: %s", body)
            self.notifier.notify_admin("ArcPay sync issue", body)
        return issues


__all__ = ["SyncValidator"]
