from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from guardian_agent import GuardianAgent
from intent_agent import IntentAgent
from payment_scheduler import PaymentScheduler
from query_agent import QueryAgent
from sync_validator import SyncValidator
from data_access import PaymentScheduleRepository

logger = logging.getLogger(__name__)

app = FastAPI(title="ArcPay API", version="0.1.0")

intent_agent = IntentAgent()
guardian_agent = GuardianAgent()
query_agent = QueryAgent()
payment_repo = PaymentScheduleRepository()
scheduler = PaymentScheduler()
validator = SyncValidator()


class CommandRequest(BaseModel):
    userId: str
    text: Optional[str] = None
    audio: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/commands")
def handle_command(body: CommandRequest) -> Dict[str, Any]:
    intent_result = intent_agent.process(body.userId, body.text, body.audio)
    entities = intent_result.entities.copy()
    if body.entities:
        entities.update(body.entities)
    payload = intent_result.to_payload()
    payload["entities"] = entities

    if intent_result.target_agent == "guardian":
        decision = guardian_agent.process(payload)
        return {
            "intent": intent_result.intent,
            "decision": decision.to_payload(),
        }
    answer = query_agent.answer(body.userId, intent_result.raw_text)
    return {
        "intent": intent_result.intent,
        "response": answer,
    }


@app.get("/v1/payments/{payment_id}")
def get_payment(payment_id: str) -> Dict[str, Any]:
    record = payment_repo.get(payment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Payment not found")
    return record


@app.post("/v1/scheduler/tick")
def scheduler_tick() -> Dict[str, Any]:
    processed = scheduler.run_tick()
    return {"processed": processed}


@app.post("/v1/system/validate")
def validate_system() -> Dict[str, Any]:
    issues = validator.validate()
    return {"issues": issues, "healthy": not issues}


__all__ = ["app"]
