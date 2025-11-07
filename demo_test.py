from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from config import load_config
from intent_agent import IntentAgent
from guardian_agent import GuardianAgent
from payment_scheduler import PaymentScheduler
from data_access import PaymentScheduleRepository


def run_demo() -> None:
    config = load_config().get("demo", {})
    user_id = config.get("userId", "demo-user")
    recipient_id = config.get("recipientId", "user2")
    amount = float(config.get("defaultAmount", 100.0))

    intent_agent = IntentAgent()
    guardian = GuardianAgent()
    scheduler = PaymentScheduler()
    payments = PaymentScheduleRepository()

    command = f"Pay {recipient_id} {amount} USDC every 5 seconds" #demo command can be updated when plugging in UI
    print(f"Command: {command}")

    intent_result = intent_agent.process(user_id=user_id, text=command)
    payload = intent_result.to_payload()
    payload_entities = payload.setdefault("entities", {})
    payload_entities.setdefault("amount", amount)
    payload_entities.setdefault("currency", "USDC")
    payload_entities.setdefault("scheduledTimestamp", (datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat())
    payload_entities.setdefault(
        "schedule",
        {"recurring": True, "frequency": "interval", "intervalSeconds": 5},
    )

    decision = guardian.process(payload)
    print(f"Guardian decision: {decision.decision} -> {decision.reason}")

    if decision.decision == "AWAITING_CONFIRMATION":
        payload_entities["confirmation"] = True
        decision = guardian.process(payload)
        print(f"Guardian confirmation result: {decision.decision} -> {decision.reason}")

    if decision.payment_id:
        print(f"Payment scheduled with id {decision.payment_id}")

    print("Waiting for scheduler...")
    for cycle in range(3):
        time.sleep(5)
        scheduler.run_tick()
        for record in payments.list(user_id):
            print(f"[cycle {cycle+1}] Payment {record['paymentId']} status: {record['status']} next at {record.get('scheduledTimestamp')}")


if __name__ == "__main__":
    run_demo()
