"""
Circle API client for wallet operations
"""
import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

API = "https://api.circle.com/v1/w3s"
API_KEY = os.getenv("CIRCLE_API_KEY", "").strip()
USER_TOKEN = os.getenv("CIRCLE_USER_TOKEN", "").strip()


class CircleAPI:
    """Circle API client"""

    def __init__(self):
        self.api_key = API_KEY
        self.user_token = USER_TOKEN
        self.base_url = API

        if not all([self.api_key, self.user_token]):
            raise ValueError("Missing CIRCLE_API_KEY or CIRCLE_USER_TOKEN in .env")

    def _get_headers(self):
        """Get API headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-User-Token": self.user_token,
            "Content-Type": "application/json"
        }

    def get_wallet_balance(self, wallet_id: str) -> dict:
        """
        Get wallet USDC balance

        Args:
            wallet_id: Circle wallet ID

        Returns:
            dict with balance information
        """
        try:
            # Get wallet details from Circle API
            resp = requests.get(
                f"{self.base_url}/wallets/{wallet_id}",
                headers=self._get_headers(),
                timeout=30
            )

            if not resp.ok:
                error = resp.json()
                raise Exception(f"Circle API error: {error.get('message', 'Unknown error')}")

            wallet_data = resp.json()["data"]["wallet"]

            # Extract balance info
            # Note: Circle API returns token balances
            balances = wallet_data.get("tokenBalances", [])

            # Find USDC balance
            usdc_balance = "0"
            for token in balances:
                if token.get("token", {}).get("symbol") == "USDC":
                    # Convert from smallest unit (6 decimals)
                    amount = int(token.get("amount", "0"))
                    usdc_balance = str(amount / 1_000_000)
                    break

            return {
                "wallet_id": wallet_id,
                "wallet_address": wallet_data.get("address"),
                "blockchain": wallet_data.get("blockchain"),
                "usdc_balance": usdc_balance,
                "raw_balances": balances
            }

        except Exception as e:
            raise Exception(f"Failed to get wallet balance: {str(e)}")

    def create_transfer(
        self,
        wallet_id: str,
        destination_address: str,
        amount_usdc: str,
        blockchain: str = "ARC-TESTNET"
    ) -> dict:
        """
        Create a USDC transfer transaction

        Args:
            wallet_id: Source wallet ID
            destination_address: Recipient address
            amount_usdc: Amount in USDC (e.g., "1.5")
            blockchain: Blockchain network

        Returns:
            dict with challenge_id for PIN approval
        """
        try:
            # Convert USDC to smallest unit (6 decimals)
            amount_units = str(int(float(amount_usdc) * 1_000_000))

            payload = {
                "idempotencyKey": str(uuid.uuid4()),
                "walletId": wallet_id,
                "blockchain": blockchain,
                "destinationAddress": destination_address,
                "amounts": [amount_units],
                "gasLimit": "100000",
                "gasPrice": "1000000000"  # 1 Gwei
            }

            resp = requests.post(
                f"{self.base_url}/user/transactions/transfer",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if not resp.ok:
                error = resp.json()
                raise Exception(
                    f"Transfer failed: {error.get('message', 'Unknown error')} "
                    f"(Code: {error.get('code', 'N/A')})"
                )

            data = resp.json()["data"]
            challenge_id = data.get("challengeId")

            return {
                "challenge_id": challenge_id,
                "status": "pending_approval",
                "message": "Transfer created, needs PIN approval"
            }

        except Exception as e:
            raise Exception(f"Failed to create transfer: {str(e)}")


# Global instance
circle_api = CircleAPI()
