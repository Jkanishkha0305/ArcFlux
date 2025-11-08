from circle.web3 import developer_controlled_wallets, utils

api_key = 'TEST_API_KEY:5e51c183a0c8db3a08e554d48208477e:3e9c863efe5a440d58bec4f862b014b6'
entity_secret = 'd0b0fe426b40075f4142b933dbe0551c22c6a49a8aa646f7cf8773c25f65b68c'

client = utils.init_developer_controlled_wallets_client(api_key=api_key, entity_secret=entity_secret)
wallets_api = developer_controlled_wallets.WalletsApi(client)

response = wallets_api.get_wallets()

print("=" * 70)
print("💰 YOUR ARC PAY WALLETS")
print("=" * 70)
print()

for wallet_obj in response.data.wallets:
    wallet = wallet_obj.actual_instance if hasattr(wallet_obj, 'actual_instance') else wallet_obj
    
    print(f"📌 {wallet.name}")
    print(f"   Wallet ID: {wallet.id}")
    print(f"   Address:   {wallet.address}")
    print(f"   Blockchain: {wallet.blockchain}")
    print(f"   Status:    {wallet.state}")
    print()

print("=" * 70)
print("✅ Currently configured in dashboard:")
print("   Wallet ID: fd492b6e-ca07-578d-8697-55bbfc55abd6")
print("   Address:   0x518866d0e6bb6fe90539bb7c833e0c053dc79c6e")
print("   💰 Has 10 USDC (from faucet)")
print("=" * 70)

