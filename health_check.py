#!/usr/bin/env python3
"""
Tippy Bot Health Check
Verify all systems are operational before deployment
"""

import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('health_check')

def check_environment():
    """Check environment variables are set"""
    logger.info("=" * 70)
    logger.info("CHECKING ENVIRONMENT VARIABLES")
    logger.info("=" * 70)
    
    required_vars = [
        'DISCORD_TOKEN',
        'MASTER_WALLET_ADDRESS',
        'MASTER_WALLET_PRIVATE_KEY',
    ]
    
    optional_vars = [
        'BLOCKCYPHER_API_KEY',
        'OWNER_DISCORD_ID',
        'OWNER_WALLET_ADDRESS',
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"  ❌ {var} - MISSING (REQUIRED)")
            missing.append(var)
        else:
            logger.info(f"  ✅ {var}")
    
    for var in optional_vars:
        if not os.getenv(var):
            logger.warning(f"  ⚠️  {var} - not set (optional)")
        else:
            logger.info(f"  ✅ {var}")
    
    return len(missing) == 0


def check_dependencies():
    """Check Python dependencies"""
    logger.info("\n" + "=" * 70)
    logger.info("CHECKING PYTHON DEPENDENCIES")
    logger.info("=" * 70)
    
    dependencies = [
        ('discord', 'discord.py'),
        ('requests', 'requests'),
        ('bitcoinlib', 'bitcoinlib'),
        ('dotenv', 'python-dotenv'),
    ]
    
    all_ok = True
    for module, package in dependencies:
        try:
            __import__(module)
            logger.info(f"  ✅ {package}")
        except ImportError:
            logger.error(f"  ❌ {package} - MISSING")
            all_ok = False
    
    return all_ok


def check_exchange_rate():
    """Test exchange rate API"""
    logger.info("\n" + "=" * 70)
    logger.info("CHECKING EXCHANGE RATE API")
    logger.info("=" * 70)
    
    try:
        from exchange_rates import get_ltc_usd_rate
        rate = get_ltc_usd_rate()
        if rate > 0:
            logger.info(f"  ✅ Exchange rate: ${rate:.2f}")
            return True
        else:
            logger.error(f"  ❌ Exchange rate returned: ${rate:.2f} (invalid)")
            return False
    except Exception as e:
        logger.error(f"  ❌ Exchange rate check failed: {e}")
        return False


def check_wallet_config():
    """Verify wallet configuration"""
    logger.info("\n" + "=" * 70)
    logger.info("CHECKING WALLET CONFIGURATION")
    logger.info("=" * 70)
    
    try:
        import config
        from address_validator import LitecoinValidator
        
        # Check master wallet
        if not config.MASTER_WALLET_ADDRESS:
            logger.error("  ❌ Master wallet address not configured")
            return False
        
        if not LitecoinValidator.validate_address(config.MASTER_WALLET_ADDRESS):
            logger.error(f"  ❌ Master wallet address invalid: {config.MASTER_WALLET_ADDRESS}")
            return False
        
        logger.info(f"  ✅ Master wallet: {config.MASTER_WALLET_ADDRESS}")
        logger.info(f"     Type: {LitecoinValidator.get_address_type(config.MASTER_WALLET_ADDRESS)}")
        
        # Check private key exists (don't print it)
        if config.MASTER_WALLET_PRIVATE_KEY:
            logger.info(f"  ✅ Master wallet private key is configured")
        else:
            logger.error(f"  ❌ Master wallet private key not configured")
            return False
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Wallet config check failed: {e}")
        return False


def check_data_dir():
    """Check if data directory exists"""
    logger.info("\n" + "=" * 70)
    logger.info("CHECKING DATA DIRECTORY")
    logger.info("=" * 70)
    
    try:
        os.makedirs('tippy_data', exist_ok=True)
        logger.info(f"  ✅ Data directory ready: tippy_data/")
        
        # Check for logs directory
        os.makedirs('tippy_data', exist_ok=True)
        logger.info(f"  ✅ Can write to tippy_data/")
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Data directory check failed: {e}")
        return False


def main():
    """Run all health checks"""
    logger.info("\n")
    logger.info("╔══════════════════════════════════════════════════════════════════════╗")
    logger.info("║                   TIPPY BOT - HEALTH CHECK                          ║")
    logger.info("╚══════════════════════════════════════════════════════════════════════╝")
    
    results = {
        "Environment Variables": check_environment(),
        "Python Dependencies": check_dependencies(),
        "Data Directory": check_data_dir(),
        "Wallet Configuration": check_wallet_config(),
        "Exchange Rate API": check_exchange_rate(),
    }
    
    logger.info("\n" + "=" * 70)
    logger.info("HEALTH CHECK SUMMARY")
    logger.info("=" * 70)
    
    all_ok = True
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status}: {check_name}")
        if not result:
            all_ok = False
    
    logger.info("=" * 70)
    
    if all_ok:
        logger.info("\n✅ All health checks passed! Bot is ready to run.\n")
        return 0
    else:
        logger.info("\n❌ Some health checks failed. Please fix the issues above.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
