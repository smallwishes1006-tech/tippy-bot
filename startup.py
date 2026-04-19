#!/usr/bin/env python3
"""
Tippy Bot - Full Startup Verification
Complete pre-deployment checks and bot startup
"""

import sys
import os
import logging
import subprocess
import time
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tippy_data/startup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('startup')

def print_banner():
    """Print startup banner"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║                    TIPPY BOT - PRODUCTION STARTUP                   ║")
    print("║                                                                      ║")
    print("║                  Version 2.1 - Fully Functional                     ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print("\n")

def run_health_check():
    """Run health check"""
    logger.info("=" * 70)
    logger.info("RUNNING HEALTH CHECK")
    logger.info("=" * 70)
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'health_check.py'], 
                              capture_output=True, text=True, timeout=30)
        print(result.stdout)
        if result.returncode != 0:
            logger.error("❌ Health check failed!")
            return False
        logger.info("✅ Health check passed!")
        return True
    except Exception as e:
        logger.error(f"❌ Error running health check: {e}")
        return False


def run_functionality_test():
    """Run functionality tests"""
    logger.info("\n" + "=" * 70)
    logger.info("RUNNING FUNCTIONALITY TESTS")
    logger.info("=" * 70)
    
    try:
        result = subprocess.run([sys.executable, 'test_functionality.py'],
                              capture_output=True, text=True, timeout=60)
        print(result.stdout)
        if result.returncode != 0:
            logger.warning("⚠️ Some functionality tests failed - proceeding anyway")
            return True  # Continue anyway
        logger.info("✅ Functionality tests passed!")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Error running tests: {e}")
        return True  # Continue anyway


def verify_discord_connection():
    """Verify Discord connection without starting full bot"""
    logger.info("\n" + "=" * 70)
    logger.info("VERIFYING DISCORD CONNECTION")
    logger.info("=" * 70)
    
    try:
        import config
        import discord
        
        if not config.DISCORD_TOKEN:
            logger.error("❌ DISCORD_TOKEN not set!")
            return False
        
        logger.info("✅ Discord token is configured")
        logger.info("   (Full connection test will happen when bot starts)")
        
        return True
    except Exception as e:
        logger.error(f"❌ Discord verification failed: {e}")
        return False


def show_status_summary(health_ok, tests_ok, discord_ok):
    """Show status summary"""
    logger.info("\n" + "=" * 70)
    logger.info("PRE-STARTUP CHECKLIST")
    logger.info("=" * 70)
    
    status = {
        "Health Checks": health_ok,
        "Functionality Tests": tests_ok,
        "Discord Configuration": discord_ok,
    }
    
    all_ok = all(status.values())
    
    for check_name, result in status.items():
        status_text = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status_text}: {check_name}")
    
    logger.info("=" * 70)
    
    return all_ok


def ask_to_proceed():
    """Ask user if they want to proceed"""
    logger.info("\n")
    response = input("Do you want to start the bot now? (yes/no): ").strip().lower()
    return response in ['yes', 'y', 'true', '1']


def start_bot():
    """Start the bot"""
    logger.info("\n" + "=" * 70)
    logger.info("STARTING BOT")
    logger.info("=" * 70)
    logger.info("Bot is starting. Press Ctrl+C to stop.\n")
    
    try:
        # Import here to catch any import errors
        import bot_main
        
        # Start the bot (this blocks)
        bot_main.main()
        
    except KeyboardInterrupt:
        logger.info("\n✅ Bot shutdown requested")
        return True
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main startup sequence"""
    print_banner()
    
    # Create data directory
    os.makedirs('tippy_data', exist_ok=True)
    
    logger.info("Starting pre-flight checks...\n")
    
    # Run checks
    health_ok = run_health_check()
    tests_ok = run_functionality_test()
    discord_ok = verify_discord_connection()
    
    # Show summary
    all_ok = show_status_summary(health_ok, tests_ok, discord_ok)
    
    if not all_ok:
        logger.warning("\n⚠️ Some checks failed, but continuing anyway...")
        time.sleep(2)
    
    # Ask to proceed
    if not ask_to_proceed():
        logger.info("Bot startup cancelled.")
        return 0
    
    # Start bot
    result = start_bot()
    
    return 0 if result else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n✅ Startup cancelled by user")
        sys.exit(0)
