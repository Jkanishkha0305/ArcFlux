"""
Quick test script for Circle API
"""
import sys
sys.path.insert(0, '.')

from circle_integration import CircleAPI
from config import settings

print("Testing Circle API...")
print(f"API Key: {settings.circle_api_key[:20]}...")
print(f"Wallet ID: {settings.circle_wallet_id}")
print("=" * 50)

try:
    circle_api = CircleAPI(
        api_key=settings.circle_api_key,
        entity_secret=settings.circle_entity_secret
    )

    # Test 1: Get balance
    print("\n1. Testing get_wallet_balance()...")
    balance = circle_api.get_wallet_balance(settings.circle_wallet_id)
    print(f"✅ Balance: {balance} USDC")

    # Test 2: Validate address
    print("\n2. Testing is_valid_address()...")
    test_address = "0xfc45b45245ca0045b208a955f619949eed194f02"
    is_valid = circle_api.is_valid_address(test_address)
    print(f"✅ Address valid: {is_valid}")

    print("\n✅ ALL TESTS PASSED!")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
