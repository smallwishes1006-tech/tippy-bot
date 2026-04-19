#!/usr/bin/env python3
"""
Tippy Bot - Production Ready
Discord Litecoin Tipping Bot with $ prefix commands
Enhanced error handling and reliability
"""

import discord
from discord.ext import commands, tasks
import logging
import sys
import os
import asyncio
import traceback

# Setup path
sys.path.insert(0, os.path.dirname(__file__))

import config
import tippy_commands

# Logging
os.makedirs('tippy_data', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tippy_data/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('tippy_bot')

# Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.guild_messages = True

# Bot setup with $ prefix
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)


def validate_startup_config():
    """Validate all critical configuration before startup"""
    logger.info('[CONFIG] Validating startup configuration...')
    
    errors = []
    warnings = []
    
    # CRITICAL: Discord token
    if not config.DISCORD_TOKEN or config.DISCORD_TOKEN == 'your_token_here':
        errors.append("DISCORD_TOKEN not set")
    
    # CRITICAL: Master wallet address
    if not config.MASTER_WALLET_ADDRESS or config.MASTER_WALLET_ADDRESS == 'your_address_here':
        errors.append("MASTER_WALLET_ADDRESS not set")
    
    # CRITICAL: Master wallet private key
    if not config.MASTER_WALLET_PRIVATE_KEY or config.MASTER_WALLET_PRIVATE_KEY == 'your_key_here':
        errors.append("MASTER_WALLET_PRIVATE_KEY not set (required for sweeps)")
    
    # CRITICAL: Network setting
    if config.NETWORK not in ['mainnet', 'testnet']:
        errors.append(f"NETWORK={config.NETWORK} - must be 'mainnet' or 'testnet'")
    
    # WARNING: BlockCypher API key (can use free tier, but limited)
    if not config.BLOCKCYPHER_API_KEY or config.BLOCKCYPHER_API_KEY == 'your_key_here':
        warnings.append("BLOCKCYPHER_API_KEY not set - using free tier (200 req/hour limit)")
    
    # WARNING: Discord bot token format (should be token)
    if config.DISCORD_TOKEN and len(config.DISCORD_TOKEN) < 50:
        warnings.append(f"DISCORD_TOKEN looks invalid (only {len(config.DISCORD_TOKEN)} chars)")
    
    # Print validation results
    if errors:
        logger.error('[CONFIG] ❌ CRITICAL CONFIGURATION ERRORS:')
        for i, error in enumerate(errors, 1):
            logger.error(f'  {i}. {error}')
        return False
    
    if warnings:
        logger.warning('[CONFIG] ⚠️  Configuration warnings:')
        for warning in warnings:
            logger.warning(f'  - {warning}')
    
    logger.info('[CONFIG] ✅ All critical configuration validated')
    return True


@bot.event
async def on_ready():
    """Bot is ready"""
    logger.info(f'[OK] Bot ready as {bot.user}')
    logger.info(f'   Watching {len(bot.guilds)} guilds')
    logger.info(f'   Prefix: $')
    
    # Start background tasks
    monitor_deposits.start()
    monitor_pending_txs.start()
    refresh_exchange_rate.start()


@bot.event
async def on_error(event, *args, **kwargs):
    """Error handler - log all bot errors"""
    logger.error(f"[ERROR] Uncaught exception in {event}:")
    logger.error(traceback.format_exc())


@tasks.loop(minutes=5)
async def monitor_deposits():
    """Monitor deposits every 5 minutes"""
    try:
        logger.info("[CHECKING] Looking for deposits to sweep...")
        from tippy_system import check_deposits
        await check_deposits(bot=bot)  # Now async, pass bot for notifications
        logger.info("[OK] Deposit check complete")
    except asyncio.TimeoutError:
        logger.error("[TIMEOUT] Deposit monitor timed out - will retry next cycle")
    except Exception as e:
        logger.error(f"[ERROR] Deposit monitor error: {e}")


@tasks.loop(minutes=25)
async def refresh_exchange_rate():
    """Refresh exchange rate every 25 minutes"""
    try:
        from exchange_rates import get_ltc_usd_rate
        rate = get_ltc_usd_rate()
        if rate > 0:
            logger.info(f"[RATE] ✅ Exchange rate refreshed: ${rate:.2f}")
        else:
            logger.warning("[RATE] ⚠️ Could not fetch exchange rate, using cached value")
    except asyncio.TimeoutError:
        logger.error("[TIMEOUT] Exchange rate refresh timed out")
    except Exception as e:
        logger.error(f"[ERROR] Exchange rate refresh error: {e}")


@tasks.loop(minutes=2)
async def monitor_pending_txs():
    """Monitor pending transactions for confirmations and expiration"""
    try:
        from tippy_system import load_all_users, save_all_users, BLOCKCYPHER_RATE_LIMITER
        import requests
        import time
        
        all_users = load_all_users()
        confirmed_count = 0
        expired_count = 0
        
        for user_id_str, user_data in all_users.items():
            pending_txs = user_data.get('pending_txs', [])
            withdrawal_history = user_data.get('withdrawal_history', [])
            
            if not pending_txs:
                continue
            
            # Check status of pending TXs
            for tx_hash in pending_txs[:]:  # Copy list to avoid modification during iteration
                try:
                    # Check if TX has expired (CRITICAL: prevent funds stuck in limbo)
                    tx_entry = None
                    for tx in withdrawal_history:
                        if tx.get('tx_hash') == tx_hash:
                            tx_entry = tx
                            break
                    
                    if tx_entry:
                        tx_age_seconds = time.time() - tx_entry.get('time', 0)
                        if tx_age_seconds > config.PENDING_TX_EXPIRATION_SECONDS:
                            # TX has expired (24+ hours unconfirmed)
                            logger.warning(f"[EXPIRED] TX {tx_hash[:20]}... is {int(tx_age_seconds/3600)} hours old - marking expired")
                            pending_txs.remove(tx_hash)
                            tx_entry['status'] = 'expired'
                            expired_count += 1
                            
                            # Notify user about expiration
                            try:
                                user = await bot.fetch_user(int(user_id_str))
                                embed = discord.Embed(
                                    title="⚠️ Transaction Expired",
                                    description=f"TX: `{tx_hash[:20]}...` has been pending for 24+ hours",
                                    color=discord.Color.orange()
                                )
                                embed.add_field(
                                    name="Next Steps",
                                    value="Please contact support or try withdrawing again",
                                    inline=False
                                )
                                await user.send(embed=embed)
                            except discord.errors.DiscordException as e:
                                logger.debug(f"Failed to notify user {user_id_str} about TX expiration: {e}")
                            
                            # Save and continue to next TX
                            all_users[user_id_str]['pending_txs'] = pending_txs
                            all_users[user_id_str]['withdrawal_history'] = withdrawal_history
                            save_all_users(all_users)
                            continue
                    
                    # Rate limit to prevent exhausting free tier
                    BLOCKCYPHER_RATE_LIMITER.wait_if_needed()
                    
                    resp = requests.get(
                        f"https://api.blockcypher.com/v1/ltc/main/txs/{tx_hash}",
                        timeout=config.BLOCKCYPHER_TIMEOUT_TX_STATUS
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        # Check for confirmations >= 6 (CRITICAL: proper confirmation check)
                        confirmations = data.get('confirmations', 0)
                        if confirmations >= config.REQUIRED_CONFIRMATIONS_DEPOSIT:
                            # TX is confirmed!
                            logger.info(f"[✅] TX {tx_hash[:20]}... confirmed ({confirmations} blocks)!")
                            pending_txs.remove(tx_hash)
                            confirmed_count += 1
                            
                            # Update history entry
                            if tx_entry:
                                tx_entry['status'] = 'confirmed'
                                tx_entry['confirmations'] = confirmations
                            
                            # Notify user
                            try:
                                user = await bot.fetch_user(int(user_id_str))
                                embed = discord.Embed(
                                    title="✅ Withdrawal Confirmed",
                                    description=f"TX: `{tx_hash[:20]}...` is now confirmed ({confirmations} blocks)!",
                                    color=discord.Color.green()
                                )
                                await user.send(embed=embed)
                            except discord.errors.DiscordException as e:
                                logger.debug(f"Failed to notify user {user_id_str} about TX confirmation: {e}")
                            
                            # Save updated data
                            all_users[user_id_str]['pending_txs'] = pending_txs
                            all_users[user_id_str]['withdrawal_history'] = withdrawal_history
                            save_all_users(all_users)
                            
                except requests.exceptions.Timeout:
                    logger.debug(f"Timeout checking TX {tx_hash[:20]}")
                except Exception as e:
                    logger.debug(f"[DEBUG] Pending TX check error for {tx_hash[:20]}: {e}")
        
        if confirmed_count > 0:
            logger.info(f"[✅] {confirmed_count} transaction(s) confirmed this cycle")
        if expired_count > 0:
            logger.warning(f"[EXPIRED] {expired_count} transaction(s) expired this cycle")
        
    except asyncio.TimeoutError:
        logger.error("[TIMEOUT] Pending TX monitor timed out")
    except Exception as e:
        logger.debug(f"[DEBUG] Pending TX monitor error: {e}")


async def load_commands():
    """Load all commands"""
    try:
        await tippy_commands.setup(bot)
        logger.info("[OK] Tippy commands loaded")
    except Exception as e:
        logger.error(f"Error loading commands: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    try:
        logger.info('=' * 70)
        logger.info('TIPPY BOT - STARTING')
        logger.info('=' * 70)
        
        # Validate critical configuration FIRST
        if not validate_startup_config():
            logger.error('[STARTUP] ❌ Cannot start - critical configuration missing')
            logger.error('[STARTUP] Please check your .env file and try again')
            return False
        
        logger.info(f'[STARTUP] Master Wallet: {config.MASTER_WALLET_ADDRESS}')
        logger.info(f'[STARTUP] Network: {config.NETWORK}')
        logger.info(f'[STARTUP] Command Prefix: $')
        logger.info(f'[STARTUP] BOT ONLINE AND LISTENING FOR COMMANDS')
        
        # Load commands before running
        import asyncio
        asyncio.run(load_commands())
        
        # Start bot with reconnect enabled
        bot.run(config.DISCORD_TOKEN, reconnect=True)
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
        return True
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
