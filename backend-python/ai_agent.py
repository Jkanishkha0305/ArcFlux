"""
============================================
AI AGENT - PAYMENT INTENT PARSER
============================================

Uses OpenAI or Anthropic to parse natural language
payment commands into structured data.

Example:
    Input: "Pay 50 USDC to Alice every week"
    Output: {
        "type": "recurring",
        "amount": 50,
        "recipient": "Alice",
        "interval": "weekly"
    }
"""

import json
from typing import Dict
from config import settings

# Import OpenAI client (v1.x style)
try:
    from openai import OpenAI
except ImportError:
    import openai
    OpenAI = None


class AIAgent:
    """
    AI-powered payment intent parser.
    
    Uses LLMs (ChatGPT or Claude) to understand
    natural language commands.
    """
    
    def __init__(self):
        self.use_openai = bool(settings.openai_api_key)
        self.use_anthropic = bool(settings.anthropic_api_key)
        
        if self.use_openai:
            if OpenAI:
                # OpenAI v1.x style
                self.client = OpenAI(api_key=settings.openai_api_key)
            else:
                # Fallback for older versions
                import openai
                openai.api_key = settings.openai_api_key
                self.client = None
            self.model = settings.ai_model
        elif self.use_anthropic:
            # Import anthropic if using it
            # import anthropic
            # self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            pass
        else:
            raise Exception("No AI API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    
    def parse_payment_intent(self, user_input: str) -> Dict:
        """
        Parse natural language into structured payment data.
        
        Args:
            user_input: Natural language command
        
        Returns:
            Dictionary with payment details
        
        Raises:
            Exception if parsing fails
        """
        
        system_prompt = """You are a payment intent parser for a blockchain payment system.

Your job is to extract payment details from natural language commands.

Extract these fields:
1. type: "recurring" or "one-time"
2. amount: numeric value in USDC
3. recipient: Ethereum address (0x...) or name
4. interval: for recurring - "daily", "weekly", "monthly", or specific like "5 minutes"
5. startDate: when to start (default: "now")

Examples:

Input: "Pay 50 USDC to Alice every week"
Output: {"type":"recurring","amount":50,"recipient":"Alice","interval":"weekly","startDate":"now"}

Input: "Send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb8 every 5 minutes"
Output: {"type":"recurring","amount":100,"recipient":"0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb8","interval":"5 minutes","startDate":"now"}

Input: "Transfer 25 USDC to Bob"
Output: {"type":"one-time","amount":25,"recipient":"Bob","interval":"none","startDate":"now"}

Respond ONLY with valid JSON, no other text."""

        try:
            if self.use_openai:
                if self.client:
                    # OpenAI v1.x style
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.1,  # Low temperature for consistent output
                        max_tokens=200
                    )
                else:
                    # Fallback for older versions
                    import openai
                    response = openai.ChatCompletion.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.1,
                        max_tokens=200
                    )
                
                ai_output = response.choices[0].message.content
            
            else:
                # Use Anthropic Claude
                # response = self.client.messages.create(
                #     model="claude-3-sonnet-20240229",
                #     messages=[{"role": "user", "content": f"{system_prompt}\n\n{user_input}"}]
                # )
                # ai_output = response.content[0].text
                raise Exception("Anthropic not configured in this example")
            
            # Parse JSON from response
            # Sometimes AI wraps JSON in markdown code blocks
            import re
            json_match = re.search(r'\{[\s\S]*\}', ai_output)
            if json_match:
                intent = json.loads(json_match.group(0))
            else:
                intent = json.loads(ai_output)
            
            # Normalize and validate
            return self._normalize_intent(intent)
        
        except Exception as e:
            print(f"Error parsing intent: {e}")
            raise Exception(f"Failed to parse payment command: {str(e)}")
    
    def _normalize_intent(self, raw_intent: Dict) -> Dict:
        """
        Clean up and validate the AI's output.
        
        Args:
            raw_intent: Raw intent from AI
        
        Returns:
            Normalized intent
        
        Raises:
            Exception if validation fails
        """
        intent = {
            "type": raw_intent.get("type", "one-time"),
            "amount": float(raw_intent.get("amount", 0)),
            "recipient": raw_intent.get("recipient", ""),
            "interval": raw_intent.get("interval", "none"),
            "startDate": raw_intent.get("startDate", "now")
        }
        
        # Validation
        if intent["amount"] <= 0:
            raise Exception("Amount must be positive")
        
        if not intent["recipient"]:
            raise Exception("Recipient is required")
        
        if intent["type"] not in ["recurring", "one-time"]:
            raise Exception("Type must be 'recurring' or 'one-time'")
        
        if intent["type"] == "recurring" and intent["interval"] == "none":
            raise Exception("Recurring payments must have an interval")
        
        return intent
    
    def handle_query(self, query: str, context: Dict) -> str:
        """
        Handle user queries about their payments.
        
        Args:
            query: User's question
            context: Current context (balance, payments, etc.)
        
        Returns:
            Natural language response
        """
        
        context_str = f"""
Current wallet balance: {context.get('balance', 'unknown')} USDC
Active payments: {context.get('activePayments', 0)}
Recent transactions: {context.get('recentTransactions', 'none')}
        """.strip()
        
        system_prompt = f"""You are a helpful payment assistant.
Answer the user's question based on this context:

{context_str}

Keep responses concise and friendly. If you don't have enough information, say so."""

        try:
            if self.use_openai:
                if self.client:
                    # OpenAI v1.x style
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": query}
                        ],
                        temperature=0.7,
                        max_tokens=150
                    )
                else:
                    # Fallback for older versions
                    import openai
                    response = openai.ChatCompletion.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": query}
                        ],
                        temperature=0.7,
                        max_tokens=150
                    )
                
                return response.choices[0].message.content
            else:
                return "Query handling not configured"
        
        except Exception as e:
            return f"Sorry, I couldn't process your query: {str(e)}"


# ============================================
# UTILITY FUNCTIONS
# ============================================

def interval_to_ms(interval: str) -> int:
    """
    Convert human-readable interval to milliseconds.
    
    Args:
        interval: e.g., "daily", "weekly", "5 minutes", "once", "none"
    
    Returns:
        Interval in milliseconds
    
    Raises:
        Exception if interval format is invalid
    """
    interval_lower = interval.lower().strip()
    
    # Handle one-time payments (execute immediately, no recurrence)
    if interval_lower in ["once", "none", "one-time", "onetime"]:
        # Return 0 for one-time payments (scheduler will execute once and stop)
        return 0
    
    # Common intervals
    intervals = {
        "daily": 24 * 60 * 60 * 1000,
        "weekly": 7 * 24 * 60 * 60 * 1000,
        "monthly": 30 * 24 * 60 * 60 * 1000,
        "hourly": 60 * 60 * 1000,
    }
    
    if interval_lower in intervals:
        return intervals[interval_lower]
    
    # Parse custom intervals like "5 minutes", "2 hours"
    import re
    match = re.match(r'(\d+)\s*(minute|hour|day|week|month)s?', interval_lower)
    
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        
        unit_ms = {
            "minute": 60 * 1000,
            "hour": 60 * 60 * 1000,
            "day": 24 * 60 * 60 * 1000,
            "week": 7 * 24 * 60 * 60 * 1000,
            "month": 30 * 24 * 60 * 60 * 1000,
        }
        
        return value * unit_ms[unit]
    
    raise Exception(f"Unsupported interval: {interval}")


# Global instance
ai_agent = AIAgent()

