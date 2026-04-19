#!/usr/bin/env python3
"""
Tippy Bot - Quick Start & Testing
Verify bot functionality before deployment
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_bot')

def test_exchange_rate():
    """Test exchange rate functionality"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST: Exchange Rate API")
    logger.info("=" * 70)
    
    try:
        from exchange_rates import get_ltc_usd_rate, ltc_to_usd, usd_to_ltc
        
        # Test rate fetching
        rate = get_ltc_usd_rate()
        logger.info(f"✅ Current LTC/USD rate: ${rate:.2f}")
        
        # Test conversions
        ltc_amount = 0.5
        usd_equivalent = ltc_to_usd(ltc_amount)
        logger.info(f"✅ {ltc_amount} LTC = ${usd_equivalent:.2f} USD")
        
        usd_amount = 10.0
        ltc_equivalent = usd_to_ltc(usd_amount)
        logger.info(f"✅ ${usd_amount:.2f} USD = {ltc_equivalent:.8f} LTC")
        
        return True
    except Exception as e:
        logger.error(f"❌ Exchange rate test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_user_account():
    """Test user account creation"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST: User Account Creation")
    logger.info("=" * 70)
    
    try:
        from tippy_system import get_user_account, load_all_users
        from address_validator import LitecoinValidator
        
        # Create/get test user
        test_user_id = 999999999
        user = get_user_account(test_user_id, "TestUser")
        
        logger.info(f"✅ User ID: {user.user_id}")
        logger.info(f"✅ Deposit Address: {user.deposit_address}")
        logger.info(f"   Address Type: {LitecoinValidator.get_address_type(user.deposit_address)}")
        logger.info(f"✅ Balance: {user.balance:.8f} LTC")
        logger.info(f"✅ Deposit Key: {user.deposit_key[:20]}...")
        
        # Verify address is valid
        if not LitecoinValidator.validate_address(user.deposit_address):
            logger.error(f"❌ Generated address is invalid: {user.deposit_address}")
            return False
        
        logger.info(f"✅ Generated address is valid")
        
        return True
    except Exception as e:
        logger.error(f"❌ User account test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_address_validation():
    """Test Litecoin address validation"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST: Address Validation")
    logger.info("=" * 70)
    
    try:
        from address_validator import LitecoinValidator
        
        # Valid addresses to test
        valid_addresses = [
            "LdG5p9gsPMNbwVwf2QXC3beFxCJYHmqv5p",  # P2PKH (Legacy)
            "Mz4qYaZzCZ5yjqhYYvQyVxp5V8B7zHPXyG",  # Testnet
            "ltc1q3upshc7g6jwd7a0w7g7zs6y2m7k5e0jrqp8yzl",  # Segwit
        ]
        
        invalid_addresses = [
            "invalid",
            "1A1z7agoat2YLZW51Wviqz1averK2",  # Bitcoin address
            "",
            "LdG5p9gsPMNbwVwf2QXC3beFxCJYHmqv5p" + "x",  # Too long
        ]
        
        logger.info("Testing VALID addresses:")
        for addr in valid_addresses:
            is_valid = LitecoinValidator.validate_address(addr)
            addr_type = LitecoinValidator.get_address_type(addr)
            status = "✅" if is_valid else "❌"
            logger.info(f"  {status} {addr} ({addr_type})")
            if not is_valid:
                logger.error(f"     ERROR: Address should be valid!")
                return False
        
        logger.info("Testing INVALID addresses:")
        for addr in invalid_addresses:
            is_valid = LitecoinValidator.validate_address(addr)
            status = "✅" if not is_valid else "❌"
            logger.info(f"  {status} {addr} (should be invalid)")
            if is_valid:
                logger.error(f"     ERROR: Address should be invalid!")
                return False
        
        logger.info(f"✅ All address validation tests passed")
        return True
    except Exception as e:
        logger.error(f"❌ Address validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_blockchain_api():
    """Test BlockCypher API connectivity"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST: BlockCypher API Connectivity")
    logger.info("=" * 70)
    
    try:
        import requests
        import config
        
        # Test basic connectivity (no auth required)
        resp = requests.get(
            'https://api.blockcypher.com/v1/ltc/main',
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            latest_block = data.get('height', 'unknown')
            logger.info(f"✅ BlockCypher is reachable")
            logger.info(f"   Latest block: #{latest_block}")
            logger.info(f"   Network: {data.get('name', 'unknown')}")
            
            # Check if API key is configured
            if config.BLOCKCYPHER_API_KEY:
                logger.info(f"✅ BlockCypher API key is configured")
            else:
                logger.warning(f"⚠️  No BlockCypher API key - using free tier (200 req/hour)")
            
            return True
        else:
            logger.error(f"❌ BlockCypher returned status {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ BlockCypher API test failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("╔══════════════════════════════════════════════════════════════════════╗")
    logger.info("║                   TIPPY BOT - FUNCTIONALITY TEST                     ║")
    logger.info("╚══════════════════════════════════════════════════════════════════════╝")
    
    results = {
        "Exchange Rate API": test_exchange_rate(),
        "Address Validation": test_address_validation(),
        "BlockCypher API": test_blockchain_api(),
        "User Account System": test_user_account(),
    }
    
    logger.info("\n" + "=" * 70)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 70)
    
    all_ok = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
        if not result:
            all_ok = False
    
    logger.info("=" * 70)
    
    if all_ok:
        logger.info("\n✅ All functionality tests passed! Bot is ready.\n")
        return 0
    else:
        logger.info("\n❌ Some tests failed. Check the output above for details.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
