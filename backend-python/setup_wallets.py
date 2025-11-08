"""
============================================
WALLET SETUP SCRIPT (Python version)
============================================

Creates Circle wallets for testing.

Usage: python setup_wallets.py
"""

import requests
import sys
from pathlib import Path
import uuid
import secrets
import base64

# Load environment
from dotenv import load_dotenv
import os

# For RSA encryption
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

load_dotenv()

CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY")
CIRCLE_API_BASE = "https://api.circle.com/v1"


def circle_request(endpoint, method="GET", json_data=None):
    """Make Circle API request"""
    url = f"{CIRCLE_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {CIRCLE_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.request(method, url, headers=headers, json=json_data)

    if not response.ok:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        sys.exit(1)

    return response.json()


def get_public_key():
    """Get Circle's public key for encryption"""
    print("🔑 Fetching Circle's public key...")
    response = circle_request("/w3s/config/entity/publicKey")

    public_key_pem = response["data"]["publicKey"]

    # Load the public key
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )

    return public_key


def generate_entity_secret():
    """Generate a secure 32-byte entity secret"""
    return secrets.token_bytes(32)


def encrypt_entity_secret(entity_secret, public_key):
    """Encrypt entity secret with Circle's public key"""
    # Encrypt using RSA-OAEP padding
    ciphertext = public_key.encrypt(
        entity_secret,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=padding.HashAlgorithm()),
            algorithm=padding.HashAlgorithm(),
            label=None
        )
    )

    # Encode to base64
    return base64.b64encode(ciphertext).decode('utf-8')


def create_wallet(wallet_set_id, name, entity_secret_ciphertext):
    """Create a wallet using W3S API"""
    print(f"💰 Creating wallet: {name}...")

    response = circle_request(
        "/w3s/developer/wallets",
        method="POST",
        json_data={
            "idempotencyKey": str(uuid.uuid4()),
            "accountType": "SCA",
            "blockchains": ["ARC-TESTNET"],
            "count": 1,
            "walletSetId": wallet_set_id,
            "entitySecretCiphertext": entity_secret_ciphertext,
            "metadata": [{
                "name": name,
                "refId": name.lower().replace(" ", "-")
            }]
        }
    )

    wallet = response["data"]["wallets"][0]
    return wallet


def create_wallet_set(entity_secret_ciphertext):
    """Create a wallet set"""
    print("📦 Creating wallet set...")

    response = circle_request(
        "/w3s/developer/walletSets",
        method="POST",
        json_data={
            "idempotencyKey": str(uuid.uuid4()),
            "name": "ArcFlux Development",
            "entitySecretCiphertext": entity_secret_ciphertext
        }
    )

    wallet_set = response["data"]["walletSet"]
    print(f"✓ Created wallet set: {wallet_set['id']}")

    return wallet_set


def update_env_file(wallet_id, entity_secret_hex):
    """Update .env file with wallet info"""
    env_path = Path(".env")

    if not env_path.exists():
        print("❌ .env file not found!")
        sys.exit(1)

    content = env_path.read_text()

    # Update values
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("CIRCLE_WALLET_ID="):
            lines[i] = f"CIRCLE_WALLET_ID={wallet_id}"
        elif line.startswith("CIRCLE_ENTITY_SECRET="):
            lines[i] = f"CIRCLE_ENTITY_SECRET={entity_secret_hex}"

    env_path.write_text("\n".join(lines))


def main():
    print("🚀 ArcFlux Wallet Setup\n")
    print("=" * 50)
    print()

    if not CIRCLE_API_KEY:
        print("❌ Error: CIRCLE_API_KEY not found in .env")
        print()
        print("Please:")
        print("1. Go to https://console.circle.com")
        print("2. Create an account (free)")
        print("3. Generate an API key")
        print("4. Add it to .env file:")
        print("   CIRCLE_API_KEY=your_key_here")
        print()
        sys.exit(1)

    try:
        # Get Circle's public key
        public_key = get_public_key()
        print("✓ Got public key")
        print()

        # Generate entity secret
        entity_secret = generate_entity_secret()
        entity_secret_hex = entity_secret.hex()
        print("✓ Generated entity secret")

        # Encrypt entity secret for API calls
        entity_secret_ciphertext = encrypt_entity_secret(entity_secret, public_key)
        print("✓ Encrypted entity secret")
        print()

        # Create wallet set
        wallet_set = create_wallet_set(entity_secret_ciphertext)
        print()

        # Re-encrypt for each wallet creation (Circle requires fresh ciphertext)
        payer_ciphertext = encrypt_entity_secret(entity_secret, public_key)
        payer_wallet = create_wallet(wallet_set["id"], "Payer Wallet", payer_ciphertext)
        print(f"✓ Payer wallet created")
        print(f"  ID: {payer_wallet['id']}")
        print(f"  Address: {payer_wallet['address']}")
        print()

        receiver_ciphertext = encrypt_entity_secret(entity_secret, public_key)
        receiver_wallet = create_wallet(wallet_set["id"], "Receiver Wallet", receiver_ciphertext)
        print(f"✓ Receiver wallet created")
        print(f"  ID: {receiver_wallet['id']}")
        print(f"  Address: {receiver_wallet['address']}")
        print()

        # Update .env
        update_env_file(payer_wallet["id"], entity_secret_hex)
        print("✓ Updated .env file with wallet IDs")
        print()

        # Instructions
        print("=" * 50)
        print("🎉 Setup Complete!")
        print()
        print("Next steps:")
        print()
        print("1. Fund your payer wallet with test USDC:")
        print("   Go to: https://faucet.circle.com")
        print(f"   Address: {payer_wallet['address']}")
        print()
        print("2. Wait 30 seconds for funds to arrive")
        print()
        print("3. Start the backend:")
        print("   python main.py")
        print()
        print("4. Test in your frontend!")
        print()
        print("📝 Save these addresses:")
        print(f"   Payer: {payer_wallet['address']}")
        print(f"   Receiver: {receiver_wallet['address']}")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
