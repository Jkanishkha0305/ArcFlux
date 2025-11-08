"""
============================================
WALLET CREATION UTILITIES
============================================

Functions to create Circle wallets for new users.
"""

import requests
import uuid
import secrets
import base64
import os
from typing import Dict, Optional
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from config import settings


def get_circle_api_base(api_key: str) -> str:
    """Determine Circle API base URL from API key type"""
    if api_key.startswith("TEST_API_KEY:"):
        return "https://api-sandbox.circle.com/v1"
    else:
        return "https://api.circle.com/v1"


def get_circle_public_key(api_key: str = None) -> object:
    """Get Circle's public key for encryption"""
    api_key = api_key or settings.circle_api_key
    if not api_key:
        raise ValueError("CIRCLE_API_KEY not configured")

    # Auto-detect correct API endpoint based on key type
    api_base = get_circle_api_base(api_key)

    url = f"{api_base}/w3s/config/entity/publicKey"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if not response.ok:
        raise Exception(f"Failed to get Circle public key: {response.status_code} - {response.text}")

    public_key_pem = response.json()["data"]["publicKey"]
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )

    return public_key


def generate_entity_secret() -> bytes:
    """Generate a secure 32-byte entity secret"""
    return secrets.token_bytes(32)


def encrypt_entity_secret(entity_secret: bytes, public_key: object) -> str:
    """Encrypt entity secret with Circle's public key"""
    ciphertext = public_key.encrypt(
        entity_secret,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(ciphertext).decode('utf-8')


def create_wallet_set(entity_secret_ciphertext: str, api_key: str = None, name: str = "ArcFlux User Wallet") -> Dict:
    """Create a wallet set for a user"""
    api_key = api_key or settings.circle_api_key
    if not api_key:
        raise ValueError("CIRCLE_API_KEY not configured")

    # Auto-detect correct API endpoint
    api_base = get_circle_api_base(api_key)

    url = f"{api_base}/w3s/developer/walletSets"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "idempotencyKey": str(uuid.uuid4()),
        "name": name,
        "entitySecretCiphertext": entity_secret_ciphertext
    }

    response = requests.post(url, headers=headers, json=data)
    if not response.ok:
        error_msg = response.text
        raise Exception(f"Failed to create wallet set: {response.status_code} - {error_msg}")

    wallet_set = response.json()["data"]["walletSet"]
    return wallet_set


def create_user_wallet(wallet_set_id: str, entity_secret_ciphertext: str, user_name: str, api_key: str = None) -> Dict:
    """Create a wallet for a user"""
    api_key = api_key or settings.circle_api_key
    if not api_key:
        raise ValueError("CIRCLE_API_KEY not configured")

    # Auto-detect correct API endpoint
    api_base = get_circle_api_base(api_key)

    url = f"{api_base}/w3s/developer/wallets"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "idempotencyKey": str(uuid.uuid4()),
        "accountType": "SCA",
        "blockchains": ["ARC-TESTNET"],
        "count": 1,
        "walletSetId": wallet_set_id,
        "entitySecretCiphertext": entity_secret_ciphertext,
        "metadata": [{
            "name": f"{user_name}'s Wallet",
            "refId": user_name.lower().replace(" ", "-")
        }]
    }

    response = requests.post(url, headers=headers, json=data)
    if not response.ok:
        error_msg = response.text
        raise Exception(f"Failed to create wallet: {response.status_code} - {error_msg}")

    wallet = response.json()["data"]["wallets"][0]
    return wallet


def create_wallet_for_user(user_name: str, user_email: str, api_key: str = None) -> Dict:
    """
    Create a complete wallet setup for a new user.
    Uses settings.circle_api_key if api_key not provided (legacy support).
    
    Returns:
        dict with keys: wallet_id, wallet_address, entity_secret (hex), wallet_set_id
    """
    try:
        # Step 1: Get Circle's public key
        public_key = get_circle_public_key(api_key)
        
        # Step 2: Generate entity secret
        entity_secret = generate_entity_secret()
        entity_secret_hex = entity_secret.hex()
        
        # Step 3: Encrypt entity secret
        entity_secret_ciphertext = encrypt_entity_secret(entity_secret, public_key)
        
        # Step 4: Create wallet set
        wallet_set = create_wallet_set(
            entity_secret_ciphertext,
            api_key=api_key,
            name=f"ArcFlux - {user_name}"
        )
        wallet_set_id = wallet_set["id"]
        
        # Step 5: Re-encrypt for wallet creation (Circle requires fresh ciphertext)
        entity_secret_ciphertext_fresh = encrypt_entity_secret(entity_secret, public_key)
        
        # Step 6: Create wallet
        wallet = create_user_wallet(
            wallet_set_id,
            entity_secret_ciphertext_fresh,
            user_name,
            api_key=api_key
        )
        
        return {
            "wallet_id": wallet["id"],
            "wallet_address": wallet["address"],
            "entity_secret": entity_secret_hex,
            "wallet_set_id": wallet_set_id
        }
    except Exception as e:
        raise Exception(f"Failed to create wallet for user: {str(e)}")


def create_wallet_for_user_with_api_key(api_key: str, user_name: str, user_email: str) -> Dict:
    """
    Create a complete wallet setup for a user with their provided API key.
    
    Args:
        api_key: User's Circle API key
        user_name: User's name
        user_email: User's email
    
    Returns:
        dict with keys: wallet_id, wallet_address, entity_secret (hex), wallet_set_id
    """
    if not api_key:
        raise ValueError("API key is required")
    
    return create_wallet_for_user(user_name, user_email, api_key=api_key)

