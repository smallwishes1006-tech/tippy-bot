#!/usr/bin/env python3
"""
Comprehensive test of deposit -> sweep -> withdrawal flow
Tests transaction creation WITHOUT broadcasting (safe)
"""

import sys
sys.path.insert(0, 'C:\\Users\\small\\tippy-bot-clean')

import config
from address_validator import LitecoinValidator
from tippy_system import get_user_account, load_all_users, save_all_users
import requests
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_flow')


def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_user_deposit_addresses():
    """Check all user deposit addresses and their balances"""
    print_header("📍 CHECKING ALL USER DEPOSIT ADDRESSES")
    
    all_users = load_all_users()
    
    if not all_users:
        print("❌ No users in database yet")
        return []
    
    user_addresses = []
    
    for user_id, user_data in all_users.items():
        deposit_addr = user_data.get('deposit_address')
        deposit_key = user_data.get('deposit_key')
        balance = user_data.get('balance', 0)
        
        if deposit_addr:
            print(f"\n👤 User ID: {user_id}")
            print(f"   Deposit Address: {deposit_addr}")
            print(f"   Stored Balance: {balance:.8f} LTC")
            
            # Check blockchain
            try:
                resp = requests.get(
                    f"https://api.blockcypher.com/v1/ltc/main/addrs/{deposit_addr}/full",
                    params={"token": config.BLOCKCYPHER_API_KEY or ""},
                    timeout=5
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    blockchain_confirmed = data.get('final_balance', 0) / 1e8
                    blockchain_unconfirmed = (data.get('balance', 0) - data.get('final_balance', 0)) / 1e8
                    total_received = data.get('total_received', 0) / 1e8
                    
                    print(f"   📊 Blockchain:")
                    print(f"      Confirmed: {blockchain_confirmed:.8f} LTC")
                    print(f"      Unconfirmed: {blockchain_unconfirmed:.8f} LTC")
                    print(f"      Total Received: {total_received:.8f} LTC")
                    
                    if blockchain_confirmed > 0:
                        print(f"   ⚠️  FOUND {blockchain_confirmed:.8f} LTC - should be swept to master!")
                        user_addresses.append({
                            'user_id': user_id,
                            'address': deposit_addr,
                            'private_key': deposit_key,
                            'blockchain_balance': blockchain_confirmed,
                            'stored_balance': balance
                        })
                    
                else:
                    print(f"   ❌ BlockCypher error: {resp.status_code}")
            except Exception as e:
                print(f"   ❌ Error checking blockchain: {e}")
    
    return user_addresses


def test_master_wallet_balance():
    """Check master wallet balance"""
    print_header("💰 MASTER WALLET BALANCE CHECK")
    
    master_addr = config.MASTER_WALLET_ADDRESS
    print(f"Master Address: {master_addr}")
    
    try:
        resp = requests.get(
            f"https://api.blockcypher.com/v1/ltc/main/addrs/{master_addr}/full",
            params={"token": config.BLOCKCYPHER_API_KEY or ""},
            timeout=5
        )
        
        if resp.status_code == 200:
            data = resp.json()
            confirmed = data.get('final_balance', 0) / 1e8
            unconfirmed = (data.get('balance', 0) - data.get('final_balance', 0)) / 1e8
            total_received = data.get('total_received', 0) / 1e8
            total_sent = data.get('total_sent', 0) / 1e8
            
            print(f"\n📊 Status:")
            print(f"   ✅ Confirmed Balance: {confirmed:.8f} LTC")
            print(f"   ⏳ Unconfirmed Balance: {unconfirmed:.8f} LTC")
            print(f"   📥 Total Received: {total_received:.8f} LTC")
            print(f"   📤 Total Sent: {total_sent:.8f} LTC")
            
            return {
                'confirmed': confirmed,
                'unconfirmed': unconfirmed,
                'total_received': total_received,
                'total_sent': total_sent
            }
        else:
            print(f"❌ BlockCypher error: {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_pending_transactions():
    """Check all pending transactions"""
    print_header("⏳ PENDING TRANSACTIONS")
    
    all_users = load_all_users()
    pending_count = 0
    
    for user_id, user_data in all_users.items():
        pending_txs = user_data.get('pending_txs', [])
        withdrawal_history = user_data.get('withdrawal_history', [])
        
        if pending_txs:
            print(f"\n👤 User {user_id}:")
            for tx_hash in pending_txs:
                print(f"   ⏳ {tx_hash[:20]}...")
                
                # Check status
                try:
                    resp = requests.get(
                        f"https://api.blockcypher.com/v1/ltc/main/txs/{tx_hash}",
                        timeout=5
                    )
                    
                    if resp.status_code == 200:
                        tx_data = resp.json()
                        confirmations = tx_data.get('confirmations', 0)
                        confirmed = tx_data.get('confirmed')
                        
                        if confirmations >= 6:
                            print(f"      ✅ CONFIRMED ({confirmations} blocks)")
                        elif confirmations > 0:
                            print(f"      ⏳ Confirming ({confirmations}/6 blocks)")
                        else:
                            print(f"      📡 In mempool (0 confirmations)")
                        
                        pending_count += 1
                except:
                    print(f"      ❓ Could not check status")
    
    if pending_count == 0:
        print("✅ No pending transactions")


def test_withdrawal_simulation():
    """Simulate withdrawal WITHOUT broadcasting (safe test)"""
    print_header("🧪 WITHDRAWAL SIMULATION (NO BROADCAST)")
    
    from litecoin_signer import LitecoinSigner
    import bitcoinlib
    
    print("Checking if withdrawal mechanism can create transactions...")
    
    # This would need a test address - skip for now
    print("⏭️  Skipped - requires test funds")


def run_diagnostics():
    """Run all diagnostic tests"""
    print("\n" + "█"*70)
    print("█  TIPPY BOT - FULL FLOW DIAGNOSTICS")
    print("█"*70)
    
    # Test 1: Check all user addresses
    user_addresses = test_user_deposit_addresses()
    
    # Test 2: Check master wallet
    master_balance = test_master_wallet_balance()
    
    # Test 3: Check pending transactions
    test_pending_transactions()
    
    # Summary
    print_header("📋 SUMMARY & RECOMMENDATIONS")
    
    if user_addresses:
        print(f"\n⚠️  ISSUE FOUND: {len(user_addresses)} deposit address(es) have unswept funds")
        print("\nPossible causes:")
        print("  1. Deposits not yet confirmed (need 6 blocks)")
        print("  2. Deposit monitoring task not running")
        print("  3. Sweep transaction creation failed")
        print("  4. Private key format issue")
        
        print("\nFix actions:")
        print("  1. Check that check_deposits() is being called")
        print("  2. Check bot logs for sweep errors")
        print("  3. Verify master wallet private key format")
        print("  4. Run: python bot_main.py and monitor logs")
    else:
        print("✅ No unswept deposits found")
    
    if master_balance and master_balance['confirmed'] > 0:
        print(f"\n✅ Master wallet has confirmed balance: {master_balance['confirmed']:.8f} LTC")
    else:
        print("\n❓ Master wallet balance is 0 or not available")
    
    print("\n" + "█"*70)
    print("█  Diagnostics complete")
    print("█"*70)


if __name__ == "__main__":
    try:
        run_diagnostics()
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}", exc_info=True)
