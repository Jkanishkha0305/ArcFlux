from __future__ import annotations

from config import load_config
from guardian_agent import GuardianAgent
from intent_agent import IntentAgent
from model_loader import HeuristicArcLLM


class DemoModelLoader:
    def __init__(self) -> None:
        self._llm = HeuristicArcLLM()

    def get(self):
        return self._llm


def run_demo() -> None:
    config = load_config().get("demo", {})
    user_id = config.get("userId", "demo-user")
    query = "Analyze my past two transactions and tell me if anything stands out"

    loader = DemoModelLoader()
    intent_agent = IntentAgent(model_loader=loader)
    guardian = GuardianAgent(model_loader=loader)

    print(f"User: {user_id}\nQuery: {query}\n")
    intent_result = intent_agent.process(user_id=user_id, text=query)
    print("Intent agent output:")
    print(f"  intent: {intent_result.intent}")
    print(f"  target_agent: {intent_result.target_agent}")
    analysis = intent_result.entities.get("analysisRequest", {})
    if analysis:
        print(f"  requested_count: {analysis.get('count')}")
        print("  transactions:")
        for tx in analysis.get("transactions", []):
            print(
                f"    - {tx.get('paymentId')} -> {tx.get('recipient')} | "
                f"{tx.get('amount')} {tx.get('currency')} | {tx.get('status')}"
            )

    payload = intent_result.to_payload()
    decision = guardian.process(payload)
    print("\nGuardian response:")
    print(f"  decision: {decision.decision}")
    print(f"  summary: {decision.reason}")


if __name__ == "__main__":
    run_demo()
