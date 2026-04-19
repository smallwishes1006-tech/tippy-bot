#!/usr/bin/env python3
"""
Bulk Sweep Script - Sweep all user deposit addresses to master wallet
Consolidates all funds from every user into the master custodial wallet
"""

import json
import os
import sys
import time
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(__file__))

import config
from tippy_system import load_all_users, UserAccount
from litecoin_signer import LitecoinSigner
from address_validator import LitecoinValidator
import requests
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tippy_data/sweep.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('bulk_sweep')


class BulkSweep:
    """Sweep all user addresses to master wallet"""
    
    def __init__(self, dry_run=True):
        """
        Initialize bulk sweep
        
        Args:
            dry_run: If True, don't actually broadcast (just show what would happen)
        """
        self.dry_run = dry_run
        self.master_address = config.MASTER_WALLET_ADDRESS
        self.master_key = config.MASTER_WALLET_PRIVATE_KEY
        self.results = {
            'total_users': 0,
            'users_with_balance': 0,
            'successful_sweeps': 0,
            'failed_sweeps': 0,
            'total_swept': 0.0,
            'sweeps': []
        }
        
        # Validate master wallet
        if not LitecoinValidator.validate_address(self.master_address):
            raise ValueError(f"Invalid master wallet address: {self.master_address}")
        
        logger.info(f"Bulk Sweep initialized (DRY RUN: {dry_run})")
        logger.info(f"Master wallet: {self.master_address}")
    
    def get_user_balances(self) -> Dict[str, dict]:
        """
        Load all users and check their blockchain balances
        
        Returns:
            Dict mapping user_id to {balance_ltc, confirmed_ltc, unconfirmed_ltc, address, key}
        """
        all_users = load_all_users()
        user_balances = {}
        
        logger.info(f"Checking {len(all_users)} users...")
        
        for user_id_str, user_data in all_users.items():
            deposit_addr = user_data.get('deposit_address')
            deposit_key = user_data.get('deposit_key')
            
            if not deposit_addr or not deposit_key:
                continue
            
            # Check balance on blockchain
            try:
                url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{deposit_addr}/full"
                resp = requests.get(
                    url,
                    params={"token": config.BLOCKCYPHER_API_KEY or ""},
                    timeout=10
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    confirmed = data.get('final_balance', 0) / 1e8
                    unconfirmed = (data.get('balance', 0) - data.get('final_balance', 0)) / 1e8
                    total = confirmed + unconfirmed
                    
                    if total > 0:
                        user_balances[user_id_str] = {
                            'address': deposit_addr,
                            'key': deposit_key,
                            'confirmed': confirmed,
                            'unconfirmed': unconfirmed,
                            'total': total
                        }
                        logger.debug(f"User {user_id_str}: {total:.8f} LTC")
                        
            except Exception as e:
                logger.warning(f"Error checking balance for {user_id_str}: {e}")
        
        return user_balances
    
    def sweep_user(self, user_id: str, address: str, private_key: str, amount: float) -> Tuple[bool, str]:
        """
        Sweep a single user's address
        
        Args:
            user_id: Discord user ID
            address: User's deposit address
            private_key: User's deposit private key
            amount: Amount to sweep in LTC
            
        Returns:
            (success, tx_hash or error_message)
        """
        try:
            # Validate address and key
            if not LitecoinValidator.validate_address(address):
                logger.error(f"User {user_id}: Invalid address {address}")
                return False, "Invalid address"
            
            if not LitecoinValidator.validate_address(self.master_address):
                logger.error(f"Invalid master address")
                return False, "Invalid master address"
            
            logger.info(f"Sweeping user {user_id}: {amount:.8f} LTC from {address[:20]}...")
            
            if self.dry_run:
                logger.info(f"  [DRY RUN] Would sweep {amount:.8f} LTC to {self.master_address}")
                return True, f"DRY_RUN"
            
            # Execute sweep
            tx_hash = LitecoinSigner.sweep_to_master(
                from_address=address,
                private_key_wif=private_key,
                amount_ltc=amount
            )
            
            if tx_hash:
                logger.info(f"✅ User {user_id} swept successfully: {tx_hash}")
                return True, tx_hash
            else:
                logger.error(f"❌ User {user_id} sweep failed: No TX hash returned")
                return False, "No TX hash returned"
                
        except Exception as e:
            logger.error(f"❌ User {user_id} sweep error: {e}")
            return False, str(e)
    
    def execute_bulk_sweep(self) -> dict:
        """
        Execute sweeps for all users with balance
        
        Returns:
            Results dict with summary
        """
        print("\n" + "="*70)
        print(f"BULK SWEEP - {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        print("="*70 + "\n")
        
        # Get all balances
        user_balances = self.get_user_balances()
        self.results['total_users'] = len(user_balances)
        
        if not user_balances:
            logger.info("No users with balance found.")
            print("\n✅ No addresses to sweep.\n")
            return self.results
        
        print(f"📊 Found {len(user_balances)} users with funds to sweep\n")
        
        # Sweep each user
        for user_id, balance_info in user_balances.items():
            self.results['users_with_balance'] += 1
            
            address = balance_info['address']
            key = balance_info['key']
            confirmed = balance_info['confirmed']
            unconfirmed = balance_info['unconfirmed']
            total = balance_info['total']
            
            print(f"User {user_id}:")
            print(f"  Address: {address[:20]}...")
            print(f"  Confirmed: {confirmed:.8f} LTC")
            print(f"  Unconfirmed: {unconfirmed:.8f} LTC")
            print(f"  Total: {total:.8f} LTC")
            
            # Sweep only confirmed balance (safe)
            if confirmed > 0:
                success, result = self.sweep_user(user_id, address, key, confirmed)
                
                if success:
                    self.results['successful_sweeps'] += 1
                    self.results['total_swept'] += confirmed
                    print(f"  ✅ Swept {confirmed:.8f} LTC")
                    print(f"  TX: {result if result != 'DRY_RUN' else 'DRY RUN'}\n")
                    
                    self.results['sweeps'].append({
                        'user_id': user_id,
                        'address': address,
                        'amount': confirmed,
                        'status': 'success',
                        'tx_hash': result
                    })
                else:
                    self.results['failed_sweeps'] += 1
                    print(f"  ❌ Failed: {result}\n")
                    
                    self.results['sweeps'].append({
                        'user_id': user_id,
                        'address': address,
                        'amount': confirmed,
                        'status': 'failed',
                        'error': result
                    })
                    
                # Rate limit to prevent API issues
                time.sleep(2)
            else:
                print(f"  ⏳ No confirmed balance yet\n")
        
        return self.results
    
    def print_summary(self):
        """Print sweep summary"""
        print("\n" + "="*70)
        print("SWEEP SUMMARY")
        print("="*70)
        print(f"Total Users: {self.results['total_users']}")
        print(f"Users with Balance: {self.results['users_with_balance']}")
        print(f"Successful Sweeps: {self.results['successful_sweeps']}")
        print(f"Failed Sweeps: {self.results['failed_sweeps']}")
        print(f"Total Amount Swept: {self.results['total_swept']:.8f} LTC")
        print(f"Master Wallet: {self.master_address}")
        print("="*70 + "\n")
        
        if self.results['failed_sweeps'] > 0:
            print("⚠️  Some sweeps failed. Check logs for details.")
        elif self.results['successful_sweeps'] > 0:
            print(f"✅ Successfully swept {self.results['total_swept']:.8f} LTC to master wallet!")
        else:
            print("ℹ️  No balances to sweep.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sweep all user addresses to master wallet')
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute live sweeps (without this flag, runs in dry-run mode)'
    )
    parser.add_argument(
        '--users',
        type=str,
        help='Comma-separated list of user IDs to sweep (leave empty for all)'
    )
    
    args = parser.parse_args()
    
    # Confirm if not dry run
    if args.execute:
        print("\n⚠️  WARNING: LIVE EXECUTION MODE")
        print("This will broadcast real transactions to Litecoin mainnet!")
        print(f"Master wallet: {config.MASTER_WALLET_ADDRESS}")
        response = input("\nType 'YES' to confirm: ")
        if response.upper() != 'YES':
            print("Aborted.")
            return
    
    try:
        sweeper = BulkSweep(dry_run=not args.execute)
        results = sweeper.execute_bulk_sweep()
        sweeper.print_summary()
        
        # Save results to JSON
        with open('tippy_data/sweep_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info("Results saved to sweep_results.json")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
