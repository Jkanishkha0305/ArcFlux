#!/usr/bin/env python3
"""
Clean Circle Wallet Setup Script
Complete workflow: Create user → Initialize PIN → Create wallet
"""
import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

API = "https://api.circle.com/v1/w3s"
API_KEY = os.getenv("CIRCLE_API_KEY", "").strip()

if not API_KEY:
    print("❌ CIRCLE_API_KEY not found in .env")
    exit(1)

print("="*70)
print("🚀 CIRCLE WALLET SETUP - FRESH START")
print("="*70)

# ============================================================================
# STEP 1: Create New User
# ============================================================================
print("\n📝 STEP 1: Creating new user...")

user_id = str(uuid.uuid4())
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

create_user_resp = requests.post(
    f"{API}/users",
    headers=headers,
    json={"userId": user_id},
    timeout=30
)

if not create_user_resp.ok:
    print(f"❌ Failed to create user: {create_user_resp.text}")
    exit(1)

print(f"✅ User created: {user_id}")

# ============================================================================
# STEP 2: Get User Token
# ============================================================================
print("\n🔑 STEP 2: Getting user token...")

token_resp = requests.post(
    f"{API}/users/token",
    headers=headers,
    json={"userId": user_id},
    timeout=30
)

if not token_resp.ok:
    print(f"❌ Failed to get token: {token_resp.text}")
    exit(1)

token_data = token_resp.json()["data"]
user_token = token_data["userToken"]
encryption_key = token_data["encryptionKey"]

print(f"✅ User token obtained")

# ============================================================================
# STEP 3: Initialize User with Wallet (creates Challenge)
# ============================================================================
print("\n🔐 STEP 3: Initializing user (creating PIN challenge)...")

init_headers = {
    "Authorization": f"Bearer {API_KEY}",
    "X-User-Token": user_token,
    "Content-Type": "application/json"
}

blockchain = "ARC-TESTNET"

init_resp = requests.post(
    f"{API}/user/initialize",
    headers=init_headers,
    json={
        "idempotencyKey": str(uuid.uuid4()),
        "accountType": "SCA",
        "blockchains": [blockchain]
    },
    timeout=30
)

if not init_resp.ok:
    print(f"❌ Failed to initialize: {init_resp.text}")

    # Try fallback blockchain
    print("\n⚠️  ARC-TESTNET failed, trying ARB-SEPOLIA...")
    blockchain = "ARB-SEPOLIA"

    init_resp = requests.post(
        f"{API}/user/initialize",
        headers=init_headers,
        json={
            "idempotencyKey": str(uuid.uuid4()),
            "accountType": "SCA",
            "blockchains": [blockchain]
        },
        timeout=30
    )

    if not init_resp.ok:
        print(f"❌ Fallback also failed: {init_resp.text}")
        exit(1)

challenge_data = init_resp.json()["data"]
challenge_id = challenge_data["challengeId"]

print(f"✅ Challenge created!")

# ============================================================================
# STEP 4: Display Instructions
# ============================================================================
print("\n" + "="*70)
print("✅ SETUP READY - NOW SET YOUR PIN")
print("="*70)

print(f"""
📋 YOUR CREDENTIALS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User ID:        {user_id}
User Token:     {user_token[:50]}...
Encryption Key: {encryption_key}
Challenge ID:   {challenge_id}
Blockchain:     {blockchain}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 NEXT STEPS:

1. Start the React app:
   cd w3s-pw-web-sdk/examples/react-example
   npm start

2. In the browser, enter these values:
   ┌─────────────────────────────────────────────────┐
   │ App ID:         {os.getenv('CIRCLE_APP_ID', '[Get from Circle Console]')}
   │ User Token:     {user_token[:40]}...
   │ Encryption Key: {encryption_key}
   │ Challenge ID:   {challenge_id}
   └─────────────────────────────────────────────────┘

3. Click "Verify Challenge"

4. SET YOUR PIN (6 digits) + Answer security questions

5. Come back and run:
   uv run check_wallet.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# Save to .env
print("\n💾 Saving to .env file...")
env_content = f"""CIRCLE_API_KEY={API_KEY}
CIRCLE_APP_ID={os.getenv('CIRCLE_APP_ID', '')}
CIRCLE_USER_ID={user_id}
CIRCLE_USER_TOKEN={user_token}
CIRCLE_ENCRYPTION_KEY={encryption_key}
CIRCLE_CHALLENGE_ID={challenge_id}
BLOCKCHAIN={blockchain}
"""

with open('.env', 'w') as f:
    f.write(env_content)

print("✅ Credentials saved to .env")
print("\n🎯 Ready for PIN setup!")
