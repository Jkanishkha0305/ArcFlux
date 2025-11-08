"""
=============================================
PAYMENT AUTOMATION AGENT
=============================================

Uses the MLAI (aimlapi) endpoint to interpret
natural-language payment commands, map them to
saved contacts, and return structured actions
that the backend can execute.
"""

import json
import re
from typing import Dict, List, Optional

from openai import OpenAI

from config import settings


class PaymentAutomationAgent:
    """LLM-powered helper that turns text into payment actions."""

    def __init__(self):
        # Prefer OpenAI, fallback to MLAI
        if settings.openai_api_key:
            self.api_key = settings.openai_api_key
            self.model = "gpt-4o-mini"  # Fast, cheap, reliable
            self.base_url = None  # Use OpenAI's default
            self.provider = "openai"
        elif settings.mlai_api_key:
            self.api_key = settings.mlai_api_key
            self.model = settings.mlai_model or "Qwen/QwQ-32B"
            self.base_url = "https://api.aimlapi.com/v1"
            self.provider = "mlai"
        else:
            self.api_key = None
            self.model = None
            self.base_url = None
            self.provider = None

        self.client: Optional[OpenAI] = None

        if self.api_key:
            try:
                if self.base_url:
                    self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
                else:
                    self.client = OpenAI(api_key=self.api_key)
                print(f"✓ Payment agent initialized with {self.provider.upper()} ({self.model})")
            except Exception as exc:  # pragma: no cover - init guard
                print(f"Failed to initialize {self.provider} client: {exc}")
                self.client = None

    @property
    def is_ready(self) -> bool:
        """Return True when the agent can reach the LLM."""

        return self.client is not None

    def plan_payment(self, command: str, contacts: List[Dict]) -> Dict:
        """Understand a payment command and map it to a contact or stock."""

        if not self.is_ready:
            raise ValueError("MLAI API key is not configured")

        if not command.strip():
            raise ValueError("Command cannot be empty")

        # Check for stock purchase intent
        stock_keywords = ["stock", "stocks", "equity", "equities", "share", "shares", "buy stock", "purchase stock"]
        command_lower = command.lower()
        is_stock_intent = any(keyword in command_lower for keyword in stock_keywords)

        if is_stock_intent:
            # Handle stock purchase intent
            return self._plan_stock_purchase(command)

        contacts_payload = [
            {
                "id": c.get("id") or c.get("contact_id"),
                "name": c.get("name"),
                "address": c.get("address"),
            }
            for c in contacts
        ]

        system_prompt = f"""You are an assistant that understands payment intents.
Given the user's saved contacts, decide if they are asking to send money.

Contacts (JSON list):
{json.dumps(contacts_payload, indent=2)}

Respond ONLY with JSON using this schema:
{{
  "action": "send_payment" | "none",
  "amount": <number>,
  "currency": "USDC",
  "contactName": <string>,
  "contactId": <string>,
  "contactAddress": <string>,
  "confidence": <number between 0 and 1>,
  "needsConfirmation": <bool>,
  "reason": <string>
}}

Rules:
- Copy contactId/contactAddress EXACTLY from the provided contact list.
- If the contact isn't in the list, leave contactId empty, contactAddress empty, and set needsConfirmation true.
- Assume currency is USDC unless user says otherwise.
- If you are unsure about the amount or contact, set needsConfirmation true.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command.strip()},
            ],
            temperature=0.2,
            max_tokens=300,
            top_p=0.7,
            frequency_penalty=0.2,
        )

        content = response.choices[0].message.content or "{}"
        plan = self._parse_json(content)

        if plan.get("currency"):
            plan["currency"] = plan["currency"].upper()

        # Resolve contact data using actual DB records to avoid hallucinations
        plan_contact = self._resolve_contact(plan, contacts)
        plan["contact"] = plan_contact

        if plan_contact:
            plan["contactId"] = plan_contact["id"]
            plan["contactAddress"] = plan_contact["address"]
            plan["contactName"] = plan_contact["name"]

        return plan

    def _resolve_contact(self, plan: Dict, contacts: List[Dict]) -> Optional[Dict]:
        """Match the agent output to a concrete contact."""

        contact_id = (plan.get("contactId") or "").strip()
        contact_addr = (plan.get("contactAddress") or "").lower()
        contact_name = (plan.get("contactName") or "").strip().lower()

        for contact in contacts:
            cid = (contact.get("id") or "").strip()
            if contact_id and cid == contact_id:
                return {
                    "id": cid,
                    "name": contact.get("name"),
                    "address": contact.get("address"),
                }

        for contact in contacts:
            addr = (contact.get("address") or "").lower()
            if contact_addr and addr == contact_addr:
                return {
                    "id": contact.get("id"),
                    "name": contact.get("name"),
                    "address": contact.get("address"),
                }

        if contact_name:
            for contact in contacts:
                if (contact.get("name") or "").strip().lower() == contact_name:
                    return {
                        "id": contact.get("id"),
                        "name": contact.get("name"),
                        "address": contact.get("address"),
                    }

        return None

    def _plan_stock_purchase(self, command: str) -> Dict:
        """Plan a stock purchase from natural language command."""
        system_prompt = """You are an assistant that understands stock purchase intents.
Extract stock purchase details from the user's command.

Respond ONLY with JSON using this schema:
{
  "action": "buy_stock",
  "amount": <number (budget for purchase)>,
  "currency": "USDC",
  "stockSymbol": <string (optional, stock ticker)>,
  "sector": <string (optional, e.g., "Banking", "Technology", "Energy")>,
  "preference": <string (optional, "value" or "growth")>,
  "confidence": <number between 0 and 1>,
  "needsConfirmation": <bool>,
  "reason": <string>
}

Rules:
- Extract budget amount if mentioned (e.g., "buy stock for 100 USDC")
- Extract stock symbol if mentioned (e.g., "buy BNKX")
- Extract sector if mentioned (e.g., "banking sector", "tech stocks")
- Extract preference if mentioned (e.g., "undervalued", "value", "growth")
- If symbol is not mentioned, set needsConfirmation true and leave stockSymbol empty.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command.strip()},
            ],
            temperature=0.2,
            max_tokens=300,
            top_p=0.7,
            frequency_penalty=0.2,
        )

        content = response.choices[0].message.content or "{}"
        plan = self._parse_json(content)

        if plan.get("action") != "buy_stock":
            plan["action"] = "buy_stock"  # Force stock purchase action

        if plan.get("currency"):
            plan["currency"] = plan["currency"].upper()

        return plan

    @staticmethod
    def _parse_json(content: str) -> Dict:
        """Extract JSON object from model output."""

        match = re.search(r"\{[\s\S]*\}", content)
        raw = match.group(0) if match else content
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "action": "none",
                "amount": 0,
                "currency": "USDC",
                "contactName": "",
                "contactId": "",
                "contactAddress": "",
                "confidence": 0,
                "needsConfirmation": True,
                "reason": "Could not parse model response",
            }


# Singleton-like helper used by FastAPI routes
payment_agent = PaymentAutomationAgent()

