from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from balance_monitor import BalanceMonitor
from data_access import PaymentScheduleRepository, UserRepository
from execution_engine import ExecutionEngine
from notification_service import NotificationService
from schedule_utils import is_recurring, next_run, parse_iso, format_iso

logger = logging.getLogger(__name__)


class PaymentScheduler:
    def __init__(self) -> None:
        self.payments = PaymentScheduleRepository()
        self.users = UserRepository()
        self.balance_monitor = BalanceMonitor()
        self.execution_engine = ExecutionEngine()
        self.notifier = NotificationService()

    def _is_due(self, payment: Dict[str, any]) -> bool:
        status = payment.get("status")
        if status not in {"APPROVED", "SCHEDULED"}:
            return False
        scheduled = payment.get("scheduledTimestamp")
        if not scheduled:
            return True
        scheduled_dt = parse_iso(scheduled)
        if not scheduled_dt:
            logger.warning("Invalid timestamp on payment %s", payment.get("paymentId"))
            return False
        return scheduled_dt <= datetime.now(timezone.utc)

    def _fetch_user(self, user_id: str) -> Optional[Dict[str, any]]:
        user = self.users.get_user(user_id)
        return user.data if user else None

    def _pre_execution_check(self, user: Dict[str, any], payment: Dict[str, any]) -> bool:
        amount = float(payment.get("amount", 0))
        if amount <= 0:
            return False
        return self.balance_monitor.ensure_sufficient(user, amount)

    def _handle_success(self, payment: Dict[str, any], result: Dict[str, any]) -> None:
        schedule = payment.get("conditions", {})
        now_iso = format_iso(datetime.now(timezone.utc))
        extras = {
            "transactionId": result.get("transaction_id"),
            "lastExecutedAt": now_iso,
        }
        if is_recurring(schedule):
            next_timestamp = next_run(schedule)
            if next_timestamp:
                extras["scheduledTimestamp"] = next_timestamp
            self.payments.update_status(payment["paymentId"], "SCHEDULED", **extras)
        else:
            self.payments.update_status(payment["paymentId"], "EXECUTED", **extras)
        print("Paid")

    def _handle_failure(self, payment_id: str, reason: str) -> None:
        updated = self.payments.update_status(payment_id, "FAILED", failureReason=reason)
        if updated:
            user = self._fetch_user(updated.get("userId"))
            if user:
                self.notifier.notify_user(user, f"Payment {payment_id} failed: {reason}")

    def run_tick(self) -> List[Dict[str, any]]:
        processed: List[Dict[str, any]] = []
        for payment in self.payments.list():
            if not self._is_due(payment):
                continue
            user = self._fetch_user(payment.get("userId"))
            if not user:
                self._handle_failure(payment["paymentId"], "User missing")
                continue
            if not self._pre_execution_check(user, payment):
                self._handle_failure(payment["paymentId"], "FAILED_INSUFFICIENT_FUNDS")
                continue
            execution = self.execution_engine.execute(payment)
            if execution.success:
                self._handle_success(payment, execution.__dict__)
            else:
                self._handle_failure(payment["paymentId"], execution.error or "execution_failed")
            processed.append({"paymentId": payment["paymentId"], "result": execution.__dict__})
        return processed


__all__ = ["PaymentScheduler"]
