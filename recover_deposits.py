#!/usr/bin/env python3
"""
Recover Previous Deposits
Check for stranded funds in old deposit addresses
"""

import sys
import logging
import requests
from address_validator import LitecoinValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('recover_deposits')

def check_address_balance(address: str) -> dict:
    """Check if an old address has any LTC balance"""
    try:
        if not LitecoinValidator.validate_address(address):
            logger.error(f"❌ Invalid address format: {address}")
            return None
        
        resp = requests.get(
            f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}",
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            confirmed_balance = data.get('final_balance', 0) / 1e8
            unconfirmed_balance = (data.get('balance', 0) - data.get('final_balance', 0)) / 1e8
            tx_count = data.get('tx_count', 0)
            
            return {
                'address': address,
                'confirmed': confirmed_balance,
                'unconfirmed': unconfirmed_balance,
                'total': confirmed_balance + unconfirmed_balance,
                'tx_count': tx_count,
                'status': 'HAS_FUNDS' if confirmed_balance > 0 else 'NO_FUNDS'
            }
        else:
            logger.error(f"BlockCypher error: {resp.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error checking address: {e}")
        return None


def main():
    """Recover deposits from old addresses"""
    logger.info("\n" + "=" * 70)
    logger.info("TIPPY BOT - DEPOSIT RECOVERY TOOL")
    logger.info("=" * 70)
    logger.info("\nThis tool checks if your old deposit addresses have any funds.\n")
    
    addresses_to_check = []
    
    print("Enter old Litecoin addresses to check (one per line).")
    print("Leave blank line when done:\n")
    
    while True:
        addr = input("Address: ").strip()
        if not addr:
            break
        addresses_to_check.append(addr)
    
    if not addresses_to_check:
        logger.warning("No addresses provided.")
        return 1
    
    logger.info(f"\n[CHECKING] {len(addresses_to_check)} address(es)...\n")
    
    found_funds = False
    results = []
    
    for addr in addresses_to_check:
        logger.info(f"Checking: {addr}")
        result = check_address_balance(addr)
        
        if result:
            results.append(result)
            
            if result['total'] > 0:
                found_funds = True
                logger.info(f"  ✅ FOUND FUNDS: {result['confirmed']:.8f} LTC (confirmed)")
                if result['unconfirmed'] > 0:
                    logger.info(f"     + {result['unconfirmed']:.8f} LTC (unconfirmed)")
                logger.info(f"  📊 Transaction count: {result['tx_count']}")
            else:
                logger.info(f"  ℹ️ No funds")
    
    if found_funds:
        logger.info("\n" + "=" * 70)
        logger.info("RECOVERY OPTIONS")
        logger.info("=" * 70)
        
        logger.info("""
If you have the PRIVATE KEY for the address, you can:

1. **Add to Current Bot** (if you have private key):
   - Edit tippy_system.py and manually add user account with private key
   - Or use sweep function to send to current master wallet
   
2. **Import Private Key** (requires privkey_wif):
   from tippy_system import get_user_account
   user = get_user_account(YOUR_USER_ID)
   user.deposit_key = "your_privkey_wif_here"  
   user.save()

3. **Manual Sweep** (requires privkey_wif):
   from litecoin_signer import LitecoinSigner
   tx_hash = LitecoinSigner.withdraw(
       from_address="old_address",
       to_address="new_address",
       amount=balance_ltc,
       private_key_wif="your_privkey_wif"
   )

4. **Use BlockChain Explorer**:
   Visit: https://blockchair.com/litecoin/
   Search your address to verify funds and transaction history
""")
    else:
        logger.info("\n✅ No stranded funds found in checked addresses.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
