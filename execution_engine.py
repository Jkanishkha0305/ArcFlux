from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from api_connector import APIConnector, APIResult

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    transaction_id: Optional[str]
    status: str
    error: Optional[str]
    raw: Dict[str, Any]


class ExecutionEngine:
    def __init__(self, api_connector: Optional[APIConnector] = None) -> None:
        self.api = api_connector or APIConnector()

    def execute(self, payment: Dict[str, Any]) -> ExecutionResult:
        payload = {
            "amount": payment.get("amount"),
            "currency": payment.get("currency", "USDC"),
            "recipient": payment.get("recipient"),
            "metadata": {"paymentId": payment.get("paymentId")},
        }
        logger.info("Triggering execution for payment %s", payment.get("paymentId"))
        response: APIResult = self.api.execute_payment(payload)
        if response.success:
            return ExecutionResult(
                success=True,
                transaction_id=response.payload.get("transactionId"),
                status=response.payload.get("status", "submitted"),
                error=None,
                raw=response.payload,
            )
        return ExecutionResult(
            success=False,
            transaction_id=None,
            status="failed",
            error=response.error,
            raw=response.payload,
        )


__all__ = ["ExecutionEngine", "ExecutionResult"]
