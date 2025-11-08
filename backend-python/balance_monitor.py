"""
============================================
BALANCE MONITOR - Proactive Alerts
============================================

Monitors wallet balance and sends alerts
when balance is low or unusual activity detected.
"""

from typing import Dict, List, Optional
from datetime import datetime
from circle_integration import CircleAPI


class BalanceAlert:
    """Represents a balance alert."""

    def __init__(
        self,
        alert_type: str,
        severity: str,
        message: str,
        current_balance: float,
        threshold: Optional[float] = None
    ):
        self.alert_type = alert_type  # "low_balance", "rapid_decrease", "warning"
        self.severity = severity  # "info", "warning", "critical"
        self.message = message
        self.current_balance = current_balance
        self.threshold = threshold
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "currentBalance": self.current_balance,
            "threshold": self.threshold,
            "timestamp": self.timestamp
        }


class BalanceMonitor:
    """Monitors balance and generates alerts."""

    def __init__(self):
        # Alert thresholds
        self.LOW_BALANCE_THRESHOLD = 10.0  # USDC
        self.CRITICAL_BALANCE_THRESHOLD = 5.0  # USDC
        print("✓ BalanceMonitor initialized")

    def check_balance(
        self,
        wallet_id: str,
        circle_api: CircleAPI,
        upcoming_payments: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Check wallet balance and generate alerts if needed.

        Returns:
            {
                "balance": float,
                "alerts": [BalanceAlert],
                "status": "healthy" | "warning" | "critical",
                "canCoverUpcoming": bool
            }
        """

        alerts: List[BalanceAlert] = []

        # Get current balance
        try:
            balance_str = circle_api.get_wallet_balance(wallet_id)
            balance = float(balance_str)
        except Exception as e:
            return {
                "balance": None,
                "alerts": [],
                "status": "error",
                "error": str(e)
            }

        # Check for low balance
        if balance <= self.CRITICAL_BALANCE_THRESHOLD:
            alerts.append(BalanceAlert(
                alert_type="low_balance",
                severity="critical",
                message=f"Critical: Balance is very low ({balance} USDC). Add funds immediately.",
                current_balance=balance,
                threshold=self.CRITICAL_BALANCE_THRESHOLD
            ))
            status = "critical"
        elif balance <= self.LOW_BALANCE_THRESHOLD:
            alerts.append(BalanceAlert(
                alert_type="low_balance",
                severity="warning",
                message=f"Warning: Balance is low ({balance} USDC). Consider adding funds soon.",
                current_balance=balance,
                threshold=self.LOW_BALANCE_THRESHOLD
            ))
            status = "warning"
        else:
            status = "healthy"

        # Check if balance can cover upcoming payments
        can_cover = True
        if upcoming_payments:
            total_upcoming = sum(p.get("amount", 0) for p in upcoming_payments)
            if total_upcoming > balance:
                can_cover = False
                alerts.append(BalanceAlert(
                    alert_type="insufficient_for_upcoming",
                    severity="critical",
                    message=f"Insufficient balance for upcoming payments. Need {total_upcoming} USDC, have {balance} USDC.",
                    current_balance=balance,
                    threshold=total_upcoming
                ))
                status = "critical"

        return {
            "balance": balance,
            "alerts": [alert.to_dict() for alert in alerts],
            "status": status,
            "canCoverUpcoming": can_cover,
            "upcomingTotal": sum(p.get("amount", 0) for p in upcoming_payments) if upcoming_payments else 0
        }

    def get_balance_health(
        self,
        wallet_id: str,
        circle_api: CircleAPI
    ) -> Dict:
        """Get simple balance health status."""

        try:
            balance_str = circle_api.get_wallet_balance(wallet_id)
            balance = float(balance_str)

            if balance <= self.CRITICAL_BALANCE_THRESHOLD:
                health = "critical"
                message = "Balance critically low"
            elif balance <= self.LOW_BALANCE_THRESHOLD:
                health = "warning"
                message = "Balance is low"
            else:
                health = "healthy"
                message = "Balance is healthy"

            return {
                "balance": balance,
                "health": health,
                "message": message
            }

        except Exception as e:
            return {
                "balance": None,
                "health": "error",
                "message": f"Error checking balance: {str(e)}"
            }


# Global instance
balance_monitor = BalanceMonitor()
