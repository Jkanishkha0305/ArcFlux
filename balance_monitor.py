from __future__ import annotations

import logging
from typing import Dict, Optional

from api_connector import APIConnector, APIResult
from notification_service import NotificationService

logger = logging.getLogger(__name__)


class BalanceMonitor:
    def __init__(self, api_connector: Optional[APIConnector] = None, notifier: Optional[NotificationService] = None) -> None:
        self.api = api_connector or APIConnector()
        self.notifier = notifier or NotificationService()
        self.cache: Dict[str, Dict[str, float]] = {}

    def get_primary_account(self, user: Dict[str, any]) -> Optional[Dict[str, any]]:
        accounts = user.get("linkedAccounts", [])
        return accounts[0] if accounts else None

    def fetch_balance(self, user: Dict[str, any]) -> Optional[APIResult]:
        account = self.get_primary_account(user)
        if not account:
            logger.warning("User %s has no linked accounts", user.get("userId"))
            return None
        result = self.api.fetch_balance(account)
        if result.success:
            self.cache.setdefault(user["userId"], {})[account["currency"]] = result.payload["balance"]
        return result

    def ensure_sufficient(self, user: Dict[str, any], required_amount: float) -> bool:
        result = self.fetch_balance(user)
        if not result or not result.success:
            return False
        balance = result.payload.get("balance", 0)
        if balance >= required_amount:
            return True
        message = (
            f"Balance check failed for {user.get('name')} — required {required_amount}, "
            f"available {balance}."
        )
        self.notifier.notify_user(user, message)
        return False

    def detect_drop(self, user: Dict[str, any], threshold: float = 0.2) -> None:
        account = self.get_primary_account(user)
        if not account:
            return
        result = self.fetch_balance(user)
        if not result or not result.success:
            return
        prev = self.cache.get(user["userId"], {}).get(account["currency"], result.payload["balance"])
        current = result.payload["balance"]
        if prev == 0:
            return
        drop_ratio = (prev - current) / prev
        if drop_ratio >= threshold:
            self.notifier.notify_user(
                user,
                f"Balance dropped by {drop_ratio:.0%}. Current balance: {current} {account['currency']}",
                channel="email",
            )


__all__ = ["BalanceMonitor"]
