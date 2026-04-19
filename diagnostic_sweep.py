#!/usr/bin/env python3
"""
Diagnostic: Check why deposits aren't sweeping
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('diagnostic')

print("\n" + "="*70)
print("DEPOSIT SWEEP DIAGNOSTIC")
print("="*70 + "\n")

# Check 1: Configuration
print("[CHECK 1] Configuration")
print("-" * 70)

if not config.MASTER_WALLET_ADDRESS:
    print("❌ MASTER_WALLET_ADDRESS not set!")
else:
    print(f"✅ MASTER_WALLET_ADDRESS: {config.MASTER_WALLET_ADDRESS}")

if not config.MASTER_WALLET_PRIVATE_KEY:
    print("❌ MASTER_WALLET_PRIVATE_KEY not set!")
else:
    print(f"✅ MASTER_WALLET_PRIVATE_KEY: {config.MASTER_WALLET_PRIVATE_KEY[:20]}...")

if not config.BLOCKCYPHER_API_KEY:
    print("⚠️  BLOCKCYPHER_API_KEY not set (will use free tier - may be rate limited)")
else:
    print(f"✅ BLOCKCYPHER_API_KEY: {config.BLOCKCYPHER_API_KEY[:20]}...")

# Check 2: User data
print("\n[CHECK 2] User Deposits")
print("-" * 70)

from tippy_system import load_all_users

users = load_all_users()
if not users:
    print("❌ No users found")
else:
    print(f"✅ Found {len(users)} user(s)")
    for user_id, user_data in list(users.items())[:5]:  # Show first 5
        addr = user_data.get('deposit_address', 'N/A')
        balance = user_data.get('balance', 0)
        print(f"   - User {user_id}: {addr} (Balance: {balance:.8f} LTC)")

# Check 3: BlockCypher connectivity
print("\n[CHECK 3] BlockCypher API")
print("-" * 70)

try:
    import requests
    resp = requests.get('https://api.blockcypher.com/v1/ltc/main', timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ BlockCypher API responsive")
        print(f"   Latest block: #{data.get('height')}")
        print(f"   Network: {data.get('name')}")
    else:
        print(f"❌ BlockCypher error: {resp.status_code}")
except Exception as e:
    print(f"❌ BlockCypher connection failed: {e}")

# Check 4: Check if any addresses have balance
print("\n[CHECK 4] Deposit Address Balances")
print("-" * 70)

try:
    import requests
    has_funds = False
    for user_id, user_data in list(users.items())[:5]:
        addr = user_data.get('deposit_address')
        if not addr:
            continue
        
        try:
            resp = requests.get(
                f"https://api.blockcypher.com/v1/ltc/main/addrs/{addr}",
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                confirmed = data.get('final_balance', 0) / 1e8
                total = data.get('balance', 0) / 1e8
                
                if total > 0:
                    has_funds = True
                    print(f"💰 {addr}")
                    print(f"   Confirmed: {confirmed:.8f} LTC")
                    print(f"   Total: {total:.8f} LTC")
                    print(f"   TX count: {data.get('tx_count')}")
        except Exception as e:
            logger.debug(f"Error checking {addr}: {e}")
    
    if not has_funds:
        print("ℹ️  No confirmed balances found on deposit addresses")
        
except Exception as e:
    print(f"❌ Error checking balances: {e}")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70 + "\n")

print("""
Next steps:
1. If MASTER_WALLET_ADDRESS or BLOCKCYPHER_API_KEY are missing, set them in .env
2. If addresses have balances but aren't sweeping, check: tippy_data/bot.log
3. Look for [SWEEP] messages to see if sweep is running
4. Check for [ERROR] messages in logs
""")
