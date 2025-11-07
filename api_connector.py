from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

from config import load_config

logger = logging.getLogger(__name__)


def _load_auth_headers() -> Dict[str, str]:
    config = load_config()
    circle_cfg = config.get("circle", {})
    api_key = circle_cfg.get("apiKey")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


@dataclass
class APIResult:
    success: bool
    payload: Dict[str, Any]
    error: Optional[str] = None


class CircleAPI:
    def __init__(self) -> None:
        self.base_url = load_config().get("circle", {}).get("apiBaseUrl", "https://api.example.com")
        self.headers = _load_auth_headers()

    def verify_address(self, address: str) -> APIResult:
        # Placeholder verification logic
        logger.debug("Verifying address %s via Circle", address)
        if address.startswith("arc1"):
            return APIResult(True, {"address": address, "status": "valid"})
        return APIResult(False, {"address": address}, error="Address failed checksum")

    def initiate_payment(self, payload: Dict[str, Any]) -> APIResult:
        logger.info("Simulating payment via Circle: %s", payload)
        # Simulate random success/failure for prototype
        if random.random() > 0.1:
            transaction_id = f"txn_{random.randint(1000, 9999)}"
            return APIResult(True, {"transactionId": transaction_id, "status": "submitted"})
        return APIResult(False, payload, error="Circle API simulated failure")


class StockDataAPI:
    def get_price(self, symbol: str) -> APIResult:
        mock_price = 100 + random.random() * 20
        logger.debug("Returning mock price for %s: %.2f", symbol, mock_price)
        return APIResult(True, {"symbol": symbol, "price": round(mock_price, 2)})


class BalanceAPI:
    def get_balance(self, account: Dict[str, Any]) -> APIResult:
        balance = float(account.get("balance", 0))
        jitter = random.uniform(-0.5, 0.5)
        value = max(0.0, balance + jitter)
        return APIResult(True, {"currency": account.get("currency", "USDC"), "balance": round(value, 2)})


class APIConnector:
    def __init__(self) -> None:
        self.circle = CircleAPI()
        self.stock = StockDataAPI()
        self.balance = BalanceAPI()

    def verify_recipient(self, address: str) -> APIResult:
        return self.circle.verify_address(address)

    def fetch_balance(self, account: Dict[str, Any]) -> APIResult:
        return self.balance.get_balance(account)

    def fetch_price(self, symbol: str) -> APIResult:
        return self.stock.get_price(symbol)

    def execute_payment(self, payload: Dict[str, Any]) -> APIResult:
        return self.circle.initiate_payment(payload)


__all__ = ["APIConnector", "APIResult"]
