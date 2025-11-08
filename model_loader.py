from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from config import load_config

logger = logging.getLogger(__name__)

try:  # pragma: no cover - import guard
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError:  # pragma: no cover - fallback when deps missing
    torch = None
    AutoTokenizer = None
    AutoModelForCausalLM = None

JSON_PATTERN = re.compile(r"\{.*\}", re.S)
STOCK_KEYWORDS = ("stock", "stocks", "equity", "equities", "share", "shares")


class BaseArcLLM:
    def classify_intent(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError

    def score_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def answer_question(self, question: str, facts: List[str]) -> str:
        raise NotImplementedError


class HuggingFaceArcLLM(BaseArcLLM):
    def __init__(self, model_name: str) -> None:
        if AutoTokenizer is None or AutoModelForCausalLM is None or torch is None:
            raise RuntimeError("transformers and torch are required for HuggingFaceArcLLM")
        self.model_name = model_name
        logger.info("Loading Hugging Face model %s", model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dtype)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

    def _generate(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.2) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        if text.startswith(prompt):
            text = text[len(prompt) :]
        return text.strip()

    def _json_response(self, prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        raw = self._generate(prompt)
        match = JSON_PATTERN.search(raw)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                logger.debug("Failed to parse JSON from model output: %s", exc)
        logger.warning("LLM returned unstructured output, using fallback")
        return fallback

    def classify_intent(self, text: str) -> Dict[str, Any]:
        prompt = (
            "You are ArcPay's intent agent. "
            "Classify the command and extract structured data. "
            "Return JSON with keys intent (make_payment|schedule_payment|stock_purchase|query|settings), "
            "confidence (0-1), and entities containing amount, currency, recipientId, "
            "scheduledTimestamp, and schedule.frequency.\n"
            f"Command: {json.dumps(text)}\nJSON:"
        )
        fallback = {"intent": "query", "confidence": 0.4, "entities": {}}
        return self._json_response(prompt, fallback)

    def score_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            "You are ArcPay's guardian risk analyst. Given the payment request details "
            "below, return JSON with riskScore (0-1) and decision (APPROVE|DENY|FLAG_FOR_REVIEW).\n"
            f"Details: {json.dumps(context, indent=2)}\nJSON:"
        )
        fallback = {"riskScore": 0.3, "decision": "APPROVE"}
        return self._json_response(prompt, fallback)

    def answer_question(self, question: str, facts: List[str]) -> str:
        fact_block = "\n".join(f"- {fact}" for fact in facts) or "- No matching records available."
        prompt = (
            "You are ArcPay's transparency agent. Using the facts below, answer the user question "
            "clearly and concisely.\nFacts:\n"
            f"{fact_block}\nQuestion: {question}\nAnswer:"
        )
        return self._generate(prompt, max_new_tokens=200, temperature=0.1)



class HeuristicArcLLM(BaseArcLLM):
    def classify_intent(self, text: str) -> Dict[str, Any]:
        lowered = text.lower()
        intent = "query"
        if any(word in lowered for word in STOCK_KEYWORDS):
            intent = "stock_purchase"
        elif any(word in lowered for word in ["pay", "send", "transfer", "purchase"]):
            intent = "make_payment"
        if intent != "stock_purchase" and any(word in lowered for word in ["schedule", "recurring", "every"]):
            intent = "schedule_payment"
        entities: Dict[str, Any] = {}
        match = re.search(r"(\d+[\.\d+]*)", lowered)
        if match:
            entities["amount"] = float(match.group(1))
        if "usdc" in lowered or "usd" in lowered:
            entities["currency"] = "USDC"
        return {"intent": intent, "confidence": 0.5, "entities": entities}

    def score_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        amount = float(context.get("amount", 0))
        features = context.get("features") or {}
        max_amount = context.get("max_amount")
        if max_amount is None:
            max_amount = features.get("max_amount", amount or 1)
        max_amount = float(max_amount or 1)
        ratio = amount / max_amount
        risk = min(1.0, ratio)
        decision = "APPROVE"
        if risk > 0.85:
            decision = "DENY"
        elif risk > 0.6:
            decision = "FLAG_FOR_REVIEW"
        return {"riskScore": round(risk, 2), "decision": decision}

    def answer_question(self, question: str, facts: List[str]) -> str:
        lines = facts or ["No records available."]
        joined = "\n".join(f"- {fact}" for fact in lines)
        return f"Here is what I found:\n{joined}"


class ModelLoader:
    def __init__(self) -> None:
        config = load_config()
        model_cfg = config.get("models", {}).get("shared", {})
        self.model_name = model_cfg.get("name", "Qwen/Qwen3-0.6B")
        self._llm: Optional[BaseArcLLM] = None

    def get(self) -> BaseArcLLM:
        if self._llm is None:
            try:
                self._llm = HuggingFaceArcLLM(self.model_name)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Falling back to heuristic model: %s", exc)
                self._llm = HeuristicArcLLM()
        return self._llm


__all__ = ["ModelLoader", "BaseArcLLM", "HuggingFaceArcLLM"]
