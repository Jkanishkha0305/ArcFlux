"""
Quick test script to create and verify a payment
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_payment():
    print("🧪 Testing ArcPay Payment System\n")

    # Step 1: Parse intent
    print("1️⃣ Parsing payment intent...")
    parse_response = requests.post(
        f"{BASE_URL}/api/parse-intent",
        json={
            "intent": "Pay 0.1 USDC to 0x518866d0e6bb6fe90539bb7c833e0c053dc79c6e every 2 minutes"
        }
    )

    if parse_response.status_code != 200:
        print(f"❌ Parse failed: {parse_response.text}")
        return

    parsed = parse_response.json()
    print(f"✅ Parsed: {json.dumps(parsed, indent=2)}\n")

    # Step 2: Create payment
    print("2️⃣ Creating payment...")
    create_response = requests.post(
        f"{BASE_URL}/api/create-payment",
        json={
            "walletId": "fd492b6e-ca07-578d-8697-55bbfc55abd6",
            "recipientAddress": parsed["recipientAddress"],
            "amount": parsed["amount"],
            "intervalMinutes": parsed["intervalMinutes"],
            "description": "Test payment"
        }
    )

    if create_response.status_code != 200:
        print(f"❌ Create failed: {create_response.text}")
        return

    payment = create_response.json()
    print(f"✅ Payment created: {payment['paymentId']}\n")

    # Step 3: Check active payments
    print("3️⃣ Checking active payments...")
    payments_response = requests.get(
        f"{BASE_URL}/api/payments",
        params={"walletId": "fd492b6e-ca07-578d-8697-55bbfc55abd6"}
    )

    if payments_response.status_code == 200:
        active = payments_response.json()
        print(f"✅ Active payments: {len(active)}\n")

    # Step 4: Wait for execution
    print("4️⃣ Waiting 2 minutes for payment to execute...")
    print("   (The scheduler runs every 60 seconds)")
    time.sleep(130)  # Wait 2 min + 10 sec buffer

    # Step 5: Check history
    print("\n5️⃣ Checking payment history...")
    history_response = requests.get(
        f"{BASE_URL}/api/history",
        params={"walletId": "fd492b6e-ca07-578d-8697-55bbfc55abd6", "limit": 5}
    )

    if history_response.status_code == 200:
        history = history_response.json()
        print(f"✅ History records: {len(history)}")
        if history:
            latest = history[0]
            print(f"\nLatest execution:")
            print(f"  Status: {latest.get('status')}")
            print(f"  Amount: {latest.get('amount')} USDC")
            print(f"  To: {latest.get('toAddress')}")
            print(f"  Tx Hash: {latest.get('transactionHash')}")

    print("\n🎉 Test complete!")

if __name__ == "__main__":
    test_payment()
