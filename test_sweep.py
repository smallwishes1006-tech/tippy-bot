#!/usr/bin/env python3
"""
Test sweep functionality - validates addresses and checks balances WITHOUT broadcasting
"""

import sys
sys.path.insert(0, 'C:\\Users\\small\\tippy-bot-clean')

import config
from address_validator import LitecoinValidator
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_master_wallet_setup():
    """Test if master wallet is properly configured"""
    
    print("\n" + "="*70)
    print("🧪 TESTING MASTER WALLET SWEEP SETUP")
    print("="*70)
    
    # 1. Check config
    print("\n1️⃣  CONFIGURATION CHECK:")
    print(f"   Master Address: {config.MASTER_WALLET_ADDRESS}")
    print(f"   Private Key (partial): {config.MASTER_WALLET_PRIVATE_KEY[:10]}...***")
    
    # 2. Validate master wallet address
    print("\n2️⃣  ADDRESS VALIDATION:")
    is_valid = LitecoinValidator.validate_address(config.MASTER_WALLET_ADDRESS)
    if is_valid:
        addr_type = LitecoinValidator.get_address_type(config.MASTER_WALLET_ADDRESS)
        print(f"   ✅ Master wallet address is VALID")
        print(f"   Type: {addr_type}")
    else:
        print(f"   ❌ Master wallet address is INVALID!")
        return False
    
    # 3. Check if private key format is valid (WIF)
    print("\n3️⃣  PRIVATE KEY FORMAT CHECK:")
    private_key = config.MASTER_WALLET_PRIVATE_KEY
    if private_key.startswith(('T', 'K', 'L')):
        print(f"   ✅ Private key format is valid (starts with {private_key[0]})")
        print(f"   Length: {len(private_key)} characters (expected: ~51-52)")
    else:
        print(f"   ❌ Private key format is INVALID (should start with T, K, or L)")
        return False
    
    # 4. Check blockchain for balance
    print("\n4️⃣  BLOCKCHAIN BALANCE CHECK:")
    try:
        url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{config.MASTER_WALLET_ADDRESS}/full"
        params = {"token": config.BLOCKCYPHER_API_KEY or ""}
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            balance_satoshis = data.get('final_balance', 0)
            balance_ltc = balance_satoshis / 1e8
            
            # Also check unconfirmed
            unconfirmed_satoshis = data.get('balance', 0) - balance_satoshis
            unconfirmed_ltc = unconfirmed_satoshis / 1e8
            
            print(f"   ✅ Blockchain query successful")
            print(f"   Confirmed Balance: {balance_ltc:.8f} LTC ({balance_satoshis} satoshis)")
            print(f"   Unconfirmed Balance: {unconfirmed_ltc:.8f} LTC ({unconfirmed_satoshis} satoshis)")
            print(f"   Total: {balance_ltc + unconfirmed_ltc:.8f} LTC")
            
            if balance_ltc > 0:
                print(f"\n   ⚠️  IMPORTANT: This wallet has {balance_ltc:.8f} LTC")
                print(f"   Any sweep operation will move REAL funds on mainnet!")
            else:
                print(f"\n   ℹ️  Wallet is empty - no funds to sweep")
            
            return True, balance_ltc
        else:
            print(f"   ❌ BlockCypher API error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False, 0
    except Exception as e:
        print(f"   ❌ Error checking balance: {e}")
        return False, 0


def test_sweep_readiness():
    """Full sweep readiness test"""
    
    success, balance = test_master_wallet_setup()
    
    if not success:
        print("\n" + "="*70)
        print("❌ SWEEP SETUP TEST FAILED")
        print("="*70)
        return False
    
    print("\n" + "="*70)
    print("✅ SWEEP IS READY - All checks passed!")
    print("="*70)
    print(f"\n📊 SWEEP STATUS:")
    print(f"   Master Wallet: {config.MASTER_WALLET_ADDRESS}")
    print(f"   Current Balance: {balance:.8f} LTC")
    print(f"   Private Key: Configured ✅")
    print(f"   Address Validation: Passed ✅")
    print(f"   Blockchain API: Working ✅")
    
    if balance > 0:
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. To sweep funds, run: python sweep_test.py --execute")
        print(f"   2. Or use: LitecoinSigner.sweep_to_master(...)")
        print(f"\n⚠️  WARNING: Sweep will move {balance:.8f} LTC on mainnet!")
        print(f"   Make sure this is intentional before executing.")
    else:
        print(f"\n💡 No funds to sweep. Send LTC to a user deposit address first.")
    
    return True


if __name__ == '__main__':
    test_sweep_readiness()
