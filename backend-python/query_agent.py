"""
============================================
QUERY AGENT - Transaction Analytics
============================================

AI-powered natural language queries about payments,
balance, transactions, and financial insights.
"""

from typing import Dict, List, Optional
from openai import OpenAI
from sqlalchemy.orm import Session
from datetime import datetime

from config import settings
from database import get_payment_history, get_user_scheduled_payments
from circle_integration import CircleAPI


class EnhancedQueryAgent:
    """AI-powered analytics for financial queries."""

    def __init__(self):
        self.client: Optional[OpenAI] = None

        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            print("✓ QueryAgent initialized with OpenAI")
        else:
            print("⚠ QueryAgent: OpenAI API key not configured")

    @property
    def is_ready(self) -> bool:
        """Check if agent is ready to handle queries."""
        return self.client is not None

    def answer_query(
        self,
        question: str,
        wallet_id: str,
        db: Session,
        circle_api: CircleAPI
    ) -> Dict:
        """
        Answer natural language questions about finances.

        Examples:
        - "What's my balance?"
        - "Show my last 5 transactions"
        - "How much did I spend this week?"
        - "Any upcoming payments?"
        - "Show me a dashboard" / "Visualize my spending" / "Generate analytics"
        """

        if not self.is_ready:
            return {
                "success": False,
                "answer": "Query agent is not available. Please configure OpenAI API key."
            }

        # Check if user is asking for a dashboard/visualization
        dashboard_keywords = ["dashboard", "visualize", "visualization", "chart", "graph", "analytics", "summary", "overview", "show me", "display"]
        question_lower = question.lower()
        should_generate_dashboard = any(keyword in question_lower for keyword in dashboard_keywords)

        # Gather context
        context = self._gather_context(wallet_id, db, circle_api)

        if should_generate_dashboard:
            # Generate dashboard data
            dashboard_data = self._generate_dashboard_data(context, wallet_id, db)
            return {
                "success": True,
                "answer": "Here's your financial dashboard with key insights and visualizations.",
                "context": context,
                "dashboard": dashboard_data
            }

        # Build AI prompt for regular queries
        prompt = f"""Answer the user's question about their finances using the provided context.

User Question: {question}

Financial Context:
{self._format_context(context)}

Provide a clear, concise answer. If the data shows numbers, include them.
If asking about transactions, summarize the relevant ones.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful financial assistant. Answer questions clearly and concisely using the provided data."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )

            answer = response.choices[0].message.content or "I couldn't generate an answer."

            return {
                "success": True,
                "answer": answer,
                "context": context
            }

        except Exception as e:
            print(f"[QUERY-AGENT] Error: {e}")
            return {
                "success": False,
                "answer": f"Error processing query: {str(e)}"
            }

    def _gather_context(
        self,
        wallet_id: str,
        db: Session,
        circle_api: CircleAPI
    ) -> Dict:
        """Gather all relevant financial data for the query."""

        context = {}

        # Get balance
        try:
            balance = circle_api.get_wallet_balance(wallet_id)
            context["balance"] = float(balance)
        except Exception as e:
            context["balance"] = None
            context["balance_error"] = str(e)

        # Get recent transactions (last 10)
        try:
            history = get_payment_history(db, wallet_id, limit=10)
            context["recentTransactions"] = [
                {
                    "id": h.id,
                    "to_address": h.to_address,
                    "amount": h.amount,
                    "status": h.status,
                    "executed_at": h.executed_at,
                    "transaction_hash": h.transaction_hash
                }
                for h in history
            ]
        except Exception as e:
            context["recentTransactions"] = []
            context["history_error"] = str(e)

        # Get scheduled payments
        try:
            scheduled = get_user_scheduled_payments(db, wallet_id)
            context["scheduledPayments"] = [
                {
                    "id": p.id,
                    "recipient": p.recipient_address,
                    "amount": p.amount,
                    "interval_ms": p.interval_ms,
                    "next_execution": p.next_execution_time,
                    "status": p.status
                }
                for p in scheduled
            ]
        except Exception as e:
            context["scheduledPayments"] = []
            context["scheduled_error"] = str(e)

        return context

    def _format_context(self, context: Dict) -> str:
        """Format context data into human-readable text for the AI."""

        lines = []

        # Balance
        if context.get("balance") is not None:
            lines.append(f"Current Balance: {context['balance']} USDC")
        else:
            lines.append("Balance: unavailable")

        # Recent transactions
        transactions = context.get("recentTransactions", [])
        if transactions:
            lines.append(f"\nRecent Transactions ({len(transactions)} total):")
            for tx in transactions[:5]:  # Show top 5
                status = tx.get("status", "unknown")
                amount = tx.get("amount", 0)
                to_addr = tx.get("to_address", "unknown")[:10] + "..."
                lines.append(f"  - {amount} USDC to {to_addr} ({status})")
        else:
            lines.append("\nRecent Transactions: None")

        # Scheduled payments
        scheduled = context.get("scheduledPayments", [])
        if scheduled:
            lines.append(f"\nScheduled Payments ({len(scheduled)} active):")
            for payment in scheduled[:3]:  # Show top 3
                amount = payment.get("amount", 0)
                recipient = payment.get("recipient", "unknown")[:10] + "..."
                interval = payment.get("interval_ms", 0)
                status = payment.get("status", "unknown")
                if interval == 0:
                    freq = "one-time"
                elif interval < 3600000:
                    freq = "frequent"
                elif interval < 86400000:
                    freq = "hourly/daily"
                else:
                    freq = "weekly/monthly"
                lines.append(f"  - {amount} USDC to {recipient} ({freq}, {status})")
        else:
            lines.append("\nScheduled Payments: None")

        return "\n".join(lines)

    def analyze_spending(
        self,
        wallet_id: str,
        db: Session,
        days: int = 7
    ) -> Dict:
        """Analyze spending patterns over a time period."""

        history = get_payment_history(db, wallet_id, limit=50)

        total_spent = 0
        transaction_count = 0
        recipients = set()

        for tx in history:
            if tx.status == "completed":
                total_spent += tx.amount
                transaction_count += 1
                recipients.add(tx.to_address)

        avg_transaction = total_spent / transaction_count if transaction_count > 0 else 0

        return {
            "totalSpent": round(total_spent, 2),
            "transactionCount": transaction_count,
            "uniqueRecipients": len(recipients),
            "averageTransaction": round(avg_transaction, 2),
            "period": f"last {days} days"
        }

    def _generate_dashboard_data(self, context: Dict, wallet_id: str, db: Session) -> Dict:
        """Generate structured dashboard data with charts and analytics."""

        # Get spending analysis
        spending_analysis = self.analyze_spending(wallet_id, db, days=30)

        # Prepare transaction data for charts
        transactions = context.get("recentTransactions", [])
        scheduled_payments = context.get("scheduledPayments", [])
        balance = context.get("balance", 0)

        # Spending over time (last 10 transactions)
        spending_over_time = []
        for tx in transactions[:10]:
            if tx.get("status") == "completed":
                spending_over_time.append({
                    "date": tx.get("executed_at", ""),
                    "amount": tx.get("amount", 0),
                    "recipient": tx.get("to_address", "unknown")[:10] + "..."
                })

        # Recipient breakdown
        recipient_breakdown = {}
        for tx in transactions:
            if tx.get("status") == "completed":
                recipient = tx.get("to_address", "unknown")[:10] + "..."
                amount = tx.get("amount", 0)
                if recipient not in recipient_breakdown:
                    recipient_breakdown[recipient] = 0
                recipient_breakdown[recipient] += amount

        # Convert to list for charts
        recipient_chart_data = [
            {"recipient": k, "amount": v}
            for k, v in sorted(recipient_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Calculate stats
        total_scheduled = sum(p.get("amount", 0) for p in scheduled_payments if p.get("status") == "active")
        active_scheduled_count = len([p for p in scheduled_payments if p.get("status") == "active"])

        # Build dashboard structure
        dashboard = {
            "summary": {
                "balance": balance,
                "totalSpent": spending_analysis["totalSpent"],
                "transactionCount": spending_analysis["transactionCount"],
                "uniqueRecipients": spending_analysis["uniqueRecipients"],
                "averageTransaction": spending_analysis["averageTransaction"],
                "activeScheduledPayments": active_scheduled_count,
                "totalScheduledAmount": round(total_scheduled, 2)
            },
            "charts": {
                "spendingOverTime": {
                    "type": "line",
                    "title": "Spending Over Time (Last 10 Transactions)",
                    "data": spending_over_time,
                    "xAxis": "date",
                    "yAxis": "amount"
                },
                "recipientBreakdown": {
                    "type": "bar",
                    "title": "Top Recipients by Amount",
                    "data": recipient_chart_data,
                    "xAxis": "recipient",
                    "yAxis": "amount"
                }
            },
            "transactions": transactions[:10],
            "scheduledPayments": scheduled_payments,
            "insights": self._generate_insights(context, spending_analysis)
        }

        return dashboard

    def _generate_insights(self, context: Dict, spending_analysis: Dict) -> List[str]:
        """Generate AI-powered insights from the data."""
        insights = []

        balance = context.get("balance", 0)
        total_spent = spending_analysis.get("totalSpent", 0)
        avg_transaction = spending_analysis.get("averageTransaction", 0)

        if balance > 0:
            insights.append(f"Your current balance is {balance:.2f} USDC.")

        if total_spent > 0:
            insights.append(f"You've spent {total_spent:.2f} USDC in the last 30 days.")
            if avg_transaction > 0:
                insights.append(f"Average transaction size: {avg_transaction:.2f} USDC.")

        transactions = context.get("recentTransactions", [])
        if len(transactions) > 0:
            insights.append(f"You have {len(transactions)} recent transactions.")

        scheduled = context.get("scheduledPayments", [])
        if len(scheduled) > 0:
            insights.append(f"You have {len(scheduled)} scheduled payments.")

        # Add spending pattern insights
        if total_spent > balance * 0.5:
            insights.append("⚠️ You've spent more than 50% of your balance in the last 30 days.")
        elif total_spent > 0:
            insights.append("✅ Your spending is within reasonable limits.")

        return insights


# Global instance
query_agent = EnhancedQueryAgent()
