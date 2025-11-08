#!/usr/bin/env python3
"""
Test script to transfer USDC directly.
"""

from circle_integration import circle_api

# Your wallet info
FROM_WALLET_ID = "fd492b6e-ca07-578d-8697-55bbfc55abd6"
TO_ADDRESS = "0x8deaefa5d170033bfacfeeaa484d4c1b91adb421"  # Receiver wallet
AMOUNT = 1.0  # USDC amount to transfer

def test_transfer():
    """Test transferring USDC"""
    print(f"🔄 Transferring {AMOUNT} USDC...")
    print(f"   From: {FROM_WALLET_ID}")
    print(f"   To: {TO_ADDRESS}")
    print()
    
    try:
        # Check balance first
        balance = circle_api.get_wallet_balance(FROM_WALLET_ID)
        print(f"💰 Current balance: {balance} USDC")
        print()
        
        if float(balance) < AMOUNT:
            print(f"❌ Insufficient balance! Need {AMOUNT} USDC, have {balance} USDC")
            return
        
        # Transfer USDC
        result = circle_api.transfer_usdc(
            from_wallet_id=FROM_WALLET_ID,
            to_address=TO_ADDRESS,
            amount=AMOUNT
        )
        
        print(f"✅ Transfer initiated!")
        print(f"   Transaction ID: {result['transactionId']}")
        print(f"   Status: {result['status']}")
        print()
        
        # Wait a bit and check status
        import time
        time.sleep(3)
        
        tx_status = circle_api.get_transaction_status(result['transactionId'])
        print(f"📊 Transaction Status:")
        print(f"   Status: {tx_status.get('status')}")
        print(f"   TxHash: {tx_status.get('txHash') or 'Pending...'}")
        print(f"   Blockchain: {tx_status.get('blockchain')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_transfer()

