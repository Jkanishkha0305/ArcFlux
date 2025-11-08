import os, uuid, requests
from dotenv import load_dotenv

load_dotenv()

API = "https://api.circle.com/v1/w3s"
API_KEY = os.getenv("CIRCLE_WEB3_API_KEY") or os.getenv("CIRCLE_API_KEY")

if not API_KEY:
    raise SystemExit("❌ CIRCLE_WEB3_API_KEY not found")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Step 1: Create user
user_id = str(uuid.uuid4())
print(f"1️⃣ Creating user: {user_id}")

create_resp = requests.post(
    f"{API}/users",
    headers=headers,
    json={"userId": user_id},
    timeout=30
)

if not create_resp.ok:
    print(f"❌ Failed: {create_resp.text}")
    exit(1)

print("✅ User created!")

# Step 2: Get user token
print("\n2️⃣ Getting user token...")

token_resp = requests.post(
    f"{API}/users/token",
    headers=headers,
    json={"userId": user_id},
    timeout=30
)

if not token_resp.ok:
    print(f"❌ Failed: {token_resp.text}")
    exit(1)

token_data = token_resp.json()["data"]
user_token = token_data["userToken"]
encryption_key = token_data["encryptionKey"]

print("✅ Token obtained!")

# Step 3: Initialize user with wallets (this creates the challenge)
print("\n3️⃣ Initializing user and creating wallet challenge...")

init_headers = {
    "Authorization": f"Bearer {API_KEY}",
    "X-User-Token": user_token,
    "Content-Type": "application/json"
}

# Try different blockchains
blockchains_to_try = [
    ("ARC-TESTNET", "SCA"),
    ("ARB-SEPOLIA", "SCA"),
    ("MATIC-AMOY", "SCA"),
    ("ETH-SEPOLIA", "SCA")
]

for blockchain, account_type in blockchains_to_try:
    print(f"\n   Trying {blockchain}...")
    
    init_resp = requests.post(
        f"{API}/user/initialize",
        headers=init_headers,
        json={
            "idempotencyKey": str(uuid.uuid4()),
            "accountType": account_type,
            "blockchains": [blockchain]
        },
        timeout=30
    )
    
    if init_resp.ok:
        challenge_data = init_resp.json()["data"]
        challenge_id = challenge_data["challengeId"]
        
        print(f"\n✅ SUCCESS! Challenge created on {blockchain}")
        print("="*70)
        print(f"User ID: {user_id}")
        print(f"User Token: {user_token[:50]}...")
        print(f"Encryption Key: {encryption_key}")
        print(f"Challenge ID: {challenge_id}")
        print(f"Blockchain: {blockchain}")
        print("="*70)
        
        print(f"\n📝 Add to .env:")
        print(f"CIRCLE_USER_ID={user_id}")
        print(f"CIRCLE_USER_TOKEN={user_token}")
        print(f"CIRCLE_ENCRYPTION_KEY={encryption_key}")
        print(f"CIRCLE_CHALLENGE_ID={challenge_id}")
        print(f"BLOCKCHAIN={blockchain}")
        
        print(f"\n⚠️  NEXT STEP REQUIRED:")
        print("   You need Circle's sample app to set the PIN")
        print("   See instructions below...")
        
        break
    else:
        print(f"   ❌ Failed: {init_resp.status_code}")
        error = init_resp.json()
        print(f"   Error: {error.get('message', 'Unknown')}")

else:
    print("\n❌ All blockchains failed")