from __future__ import annotations

import time
from typing import List, Dict, Any

from config import load_config
from data_access import PaymentScheduleRepository
from guardian_agent import GuardianAgent
from intent_agent import IntentAgent
from model_loader import HeuristicArcLLM
from payment_scheduler import PaymentScheduler
from stock_agent import StockSelectionAgent


class DemoModelLoader:
    """For demo purposes we keep everything on the lightweight heuristic model."""

    def __init__(self) -> None:
        self._llm = HeuristicArcLLM()

    def get(self):
        return self._llm


def _print_recommendations(recommendations: List[Dict[str, Any]]) -> None:
    print("\nI found these reasonably valued candidates:\n")
    for idx, item in enumerate(recommendations, start=1):
        print(
            f"  {idx}. {item['symbol']} ({item['name']}) "
            f"- {item['sector']} | Price {item['price']} USDC | "
            f"P/E {item['peRatio']} | Discount {item['discountToPeersPct']}% | "
            f"Score {item['valuationScore']}"
        )
        print(f"     ↳ {item['memo']}")
    print("")


def _prompt_selection(default_symbol: str) -> str:
    raw = input(f"Select a stock symbol [{default_symbol}]: ").strip().upper()
    return raw or default_symbol


def run_stock_purchase_demo() -> None:
    config = load_config().get("demo", {})
    user_id = config.get("userId", "demo-user")
    query = (
        "Find a stock banking sector and purchase it for 100 USDC least value compared to its peers"
    )

    model_loader = DemoModelLoader()
    intent_agent = IntentAgent(model_loader=model_loader)
    stock_agent = StockSelectionAgent()
    guardian = GuardianAgent(model_loader=model_loader)
    scheduler = PaymentScheduler()
    payment_repo = PaymentScheduleRepository()

    print(f"User ({user_id}) command: {query}")
    intent_result = intent_agent.process(user_id=user_id, text=query)
    payload = intent_result.to_payload()

    stock_stage = stock_agent.process(payload)
    if stock_stage.get("status") != "AWAITING_SELECTION":
        print("Unexpected stock response:", stock_stage)
        return

    recommendations = stock_stage["recommendations"]
    _print_recommendations(recommendations)
    chosen_symbol = _prompt_selection(recommendations[0]["symbol"])
    payload["entities"]["selectedStock"] = chosen_symbol

    stock_stage = stock_agent.process(payload)
    if stock_stage.get("status") != "READY_FOR_GUARDIAN":
        print("Selection was not accepted:", stock_stage.get("message"))
        return

    guardian_decision = guardian.process(stock_stage["payload"])
    if guardian_decision.decision == "AWAITING_CONFIRMATION":
        print("Guardian requested confirmation. Auto-confirming for demo.")
        stock_stage["payload"]["entities"]["confirmation"] = True
        guardian_decision = guardian.process(stock_stage["payload"])

    print(
        f"Guardian decision: {guardian_decision.decision} "
        f"({guardian_decision.reason})"
    )

    if not guardian_decision.payment_id:
        print("No payment scheduled. Demo ends here.")
        return

    print(f"Payment scheduled with id {guardian_decision.payment_id}.")
    print("Running scheduler tick to simulate execution...")
    time.sleep(1)
    scheduler.run_tick()
    record = payment_repo.get(guardian_decision.payment_id)
    if record:
        print(
            f"Payment {record['paymentId']} now {record['status']} "
            f"next run at {record.get('scheduledTimestamp')}"
        )


if __name__ == "__main__":
    run_stock_purchase_demo()
