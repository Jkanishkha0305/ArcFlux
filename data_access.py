from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import get_path
from data_store import JSONDataStore


@dataclass
class User:
    userId: str
    data: Dict[str, Any]

    @property
    def preferences(self) -> Dict[str, Any]:
        return self.data.get("preferences", {})

    @property
    def whitelisted_recipients(self) -> List[Dict[str, Any]]:
        return self.data.get("whitelistedRecipients", [])


class UserRepository:
    def __init__(self) -> None:
        self.store = JSONDataStore(get_path("userDatabase"), default_factory=list)

    def list_users(self) -> List[User]:
        return [User(item["userId"], item) for item in self.store.load()]

    def get_user(self, user_id: str) -> Optional[User]:
        for record in self.store.load():
            if record.get("userId") == user_id:
                return User(record["userId"], record)
        return None

    def upsert(self, user: Dict[str, Any]) -> None:
        def _mutator(data):
            for idx, record in enumerate(data):
                if record.get("userId") == user["userId"]:
                    data[idx] = user
                    break
            else:
                data.append(user)
            return data

        self.store.update(_mutator)


class PaymentScheduleRepository:
    def __init__(self) -> None:
        self.store = JSONDataStore(get_path("paymentSchedule"), default_factory=list)

    def list(self, filter_user: Optional[str] = None) -> List[Dict[str, Any]]:
        payments = self.store.load()
        if filter_user:
            return [p for p in payments if p.get("userId") == filter_user]
        return payments

    def get(self, payment_id: str) -> Optional[Dict[str, Any]]:
        for record in self.store.load():
            if record.get("paymentId") == payment_id:
                return record
        return None

    def upsert(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        payment.setdefault("updatedAt", datetime.now(timezone.utc).isoformat())

        def _mutator(data):
            for idx, record in enumerate(data):
                if record.get("paymentId") == payment["paymentId"]:
                    payment.setdefault("createdAt", record.get("createdAt"))
                    data[idx] = payment
                    break
            else:
                payment.setdefault("createdAt", datetime.now(timezone.utc).isoformat())
                data.append(payment)
            return data

        self.store.update(_mutator)
        return payment

    def update_status(self, payment_id: str, status: str, **extras: Any) -> Optional[Dict[str, Any]]:
        updated: Optional[Dict[str, Any]] = None

        def _mutator(data):
            nonlocal updated
            for record in data:
                if record.get("paymentId") == payment_id:
                    record["status"] = status
                    record.update(extras)
                    record["updatedAt"] = datetime.now(timezone.utc).isoformat()
                    updated = record
                    break
            return data

        self.store.update(_mutator)
        return updated


class RiskAssessmentRepository:
    def __init__(self) -> None:
        self.store = JSONDataStore(get_path("riskAssessmentDb"), default_factory=list)

    def append(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        assessment.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        self.store.append(assessment)
        return assessment

    def list(self) -> List[Dict[str, Any]]:
        return self.store.load()


class StockRepository:
    def __init__(self) -> None:
        self.store = JSONDataStore(get_path("stockMarketDb"), default_factory=list)

    def list_all(self) -> List[Dict[str, Any]]:
        return self.store.load()

    def list_by_sector(self, sector: Optional[str]) -> List[Dict[str, Any]]:
        records = self.list_all()
        if not sector:
            return records
        wanted = sector.lower()
        return [record for record in records if record.get("sector", "").lower() == wanted]

    def find(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not symbol:
            return None
        normalized = symbol.upper()
        for record in self.list_all():
            if record.get("symbol", "").upper() == normalized:
                return record
        return None


__all__ = [
    "UserRepository",
    "PaymentScheduleRepository",
    "RiskAssessmentRepository",
    "User",
    "StockRepository",
]
