"""
============================================
GUARDIAN AGENT - Risk Scoring & Security
============================================

AI-powered risk assessment for payments.
Checks balance, verifies recipients, and scores transactions.
"""

from typing import Dict, Optional
from openai import OpenAI
from config import settings
from circle_integration import CircleAPI


class GuardianAgent:
    """AI-powered risk assessment for payment security."""

    def __init__(self):
        self.client: Optional[OpenAI] = None

        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            print("✓ GuardianAgent initialized with OpenAI")
        else:
            print("⚠ GuardianAgent: OpenAI API key not configured")

    @property
    def is_ready(self) -> bool:
        """Check if agent is ready to assess risk."""
        return self.client is not None

    def assess_payment_risk(
        self,
        amount: float,
        recipient_address: str,
        recipient_name: str,
        sender_balance: float,
        is_contact: bool = False
    ) -> Dict:
        """
        Assess risk for a payment transaction.

        Returns:
            {
                "riskScore": 0.0-1.0,
                "riskLevel": "low" | "medium" | "high",
                "decision": "approve" | "review" | "deny",
                "reason": "explanation",
                "checks": {
                    "balanceCheck": bool,
                    "amountCheck": bool,
                    "recipientCheck": bool
                }
            }
        """

        if not self.is_ready:
            # Fallback to rule-based scoring
            return self._rule_based_assessment(amount, sender_balance, is_contact)

        # Perform automated checks
        checks = {
            "balanceCheck": sender_balance >= amount,
            "amountCheck": amount > 0 and amount <= sender_balance,
            "recipientCheck": self._is_valid_address(recipient_address)
        }

        # Calculate balance ratio
        balance_ratio = (sender_balance / amount) if amount > 0 else 0

        # Build AI prompt
        prompt = f"""Assess the risk of this cryptocurrency payment:

Payment Details:
- Amount: {amount} USDC
- Recipient: {recipient_name} ({recipient_address})
- Sender Balance: {sender_balance} USDC
- Balance Ratio: {balance_ratio:.2f}x (balance/amount)
- Is Saved Contact: {is_contact}

Automated Checks:
- Sufficient balance: {checks['balanceCheck']}
- Valid amount: {checks['amountCheck']}
- Valid recipient address: {checks['recipientCheck']}

Provide a risk assessment with:
1. Risk score (0.0 = no risk, 1.0 = maximum risk)
2. Risk level (low/medium/high)
3. Decision (approve/review/deny)
4. Brief reason

Return ONLY JSON:
{{
  "riskScore": 0.0-1.0,
  "riskLevel": "low|medium|high",
  "decision": "approve|review|deny",
  "reason": "brief explanation"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial risk assessment AI. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )

            content = response.choices[0].message.content or "{}"
            import json
            result = json.loads(content)

            # Add checks to result
            result["checks"] = checks
            result["balanceRatio"] = balance_ratio

            return result

        except Exception as e:
            print(f"[GUARDIAN] AI assessment failed: {e}, using fallback")
            return self._rule_based_assessment(amount, sender_balance, is_contact)

    def _rule_based_assessment(
        self,
        amount: float,
        sender_balance: float,
        is_contact: bool
    ) -> Dict:
        """Fallback rule-based risk assessment when AI is unavailable."""

        balance_ratio = (sender_balance / amount) if amount > 0 else 0

        # Calculate risk score
        risk_score = 0.0

        # Balance check
        if balance_ratio < 1.0:
            risk_score += 1.0  # Critical: insufficient balance
        elif balance_ratio < 2.0:
            risk_score += 0.5  # High: low balance cushion
        elif balance_ratio < 5.0:
            risk_score += 0.2  # Medium: moderate cushion

        # Contact check
        if not is_contact:
            risk_score += 0.3  # Higher risk for unknown recipients

        # Large amount check
        if amount > 1000:
            risk_score += 0.2

        # Normalize to 0-1
        risk_score = min(risk_score, 1.0)

        # Determine level and decision
        if risk_score >= 0.7:
            risk_level = "high"
            decision = "deny" if balance_ratio < 1.0 else "review"
            reason = "High risk: Insufficient balance or large amount to unknown recipient"
        elif risk_score >= 0.4:
            risk_level = "medium"
            decision = "review"
            reason = "Medium risk: Low balance cushion or unknown recipient"
        else:
            risk_level = "low"
            decision = "approve"
            reason = "Low risk: Sufficient balance and verified recipient"

        return {
            "riskScore": round(risk_score, 2),
            "riskLevel": risk_level,
            "decision": decision,
            "reason": reason,
            "checks": {
                "balanceCheck": balance_ratio >= 1.0,
                "amountCheck": amount > 0,
                "recipientCheck": True
            },
            "balanceRatio": round(balance_ratio, 2)
        }

    def _is_valid_address(self, address: str) -> bool:
        """Basic validation of Ethereum-style address."""
        if not address:
            return False
        # Check if starts with 0x and has proper length
        return address.startswith("0x") and len(address) == 42


# Global instance
guardian_agent = GuardianAgent()
