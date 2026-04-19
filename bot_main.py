#!/usr/bin/env python3
"""
Tippy Bot - Production Ready
Discord Litecoin Tipping Bot with $ prefix commands
"""

import discord
from discord.ext import commands, tasks
import logging
import sys
import os

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
    """Error handler"""
    logger.error(f"Error in {event}:", exc_info=True)


@tasks.loop(minutes=5)
async def monitor_deposits():
    """Monitor deposits every 5 minutes"""
    try:
        logger.info("[CHECKING] Looking for deposits to sweep...")
        from tippy_system import check_deposits
        await check_deposits(bot=bot)  # Now async, pass bot for notifications
        logger.info("[OK] Deposit check complete")
    except Exception as e:
        logger.error(f"Deposit monitor error: {e}")


@tasks.loop(minutes=25)
async def refresh_exchange_rate():
    """Refresh exchange rate every 25 minutes"""
    try:
        from exchange_rates import get_ltc_usd_rate
        rate = get_ltc_usd_rate()
        logger.info(f"[RATE] ✅ Exchange rate refreshed: ${rate:.2f}")
    except Exception as e:
        logger.error(f"Exchange rate refresh error: {e}")


@tasks.loop(minutes=2)
async def monitor_pending_txs():
    """Monitor pending transactions for confirmations"""
    try:
        from tippy_system import load_all_users
        import requests
        
        all_users = load_all_users()
        
        for user_id_str, user_data in all_users.items():
            pending_txs = user_data.get('pending_txs', [])
            withdrawal_history = user_data.get('withdrawal_history', [])
            
            if not pending_txs:
                continue
            
            # Check status of pending TXs
            for tx_hash in pending_txs[:]:  # Copy list to avoid modification during iteration
                try:
                    resp = requests.get(
                        f"https://api.blockcypher.com/v1/ltc/main/txs/{tx_hash}",
                        timeout=5
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if "confirmed" in data and data["confirmed"]:
                            # TX is confirmed!
                            logger.info(f"[OK] TX {tx_hash[:20]}... confirmed!")
                            pending_txs.remove(tx_hash)
                            
                            # Update history entry
                            for tx_entry in withdrawal_history:
                                if tx_entry.get('tx_hash') == tx_hash:
                                    tx_entry['status'] = 'confirmed'
                            
                            # Notify user
                            try:
                                user = await bot.fetch_user(int(user_id_str))
                                embed = discord.Embed(
                                    title="Withdrawal Confirmed",
                                    description=f"TX: `{tx_hash[:20]}...` is now confirmed!",
                                    color=discord.Color.green()
                                )
                                await user.send(embed=embed)
                            except:
                                pass
                            
                            # Save updated data
                            from tippy_system import UserAccount, save_all_users
                            all_users[user_id_str]['pending_txs'] = pending_txs
                            all_users[user_id_str]['withdrawal_history'] = withdrawal_history
                            save_all_users(all_users)
                            
                except Exception as e:
                    logger.debug(f"Pending TX check error for {tx_hash[:20]}: {e}")
        
    except Exception as e:
        logger.debug(f"Pending TX monitor error: {e}")


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
        
        # Verify config
        if not config.DISCORD_TOKEN:
            logger.error("ERROR: DISCORD_TOKEN not set in config")
            return False
        
        if not config.MASTER_WALLET_ADDRESS:
            logger.error("ERROR: MASTER_WALLET_ADDRESS not set in config")
            return False
        
        logger.info(f'Master Wallet: {config.MASTER_WALLET_ADDRESS}')
        logger.info(f'Command Prefix: $')
        logger.info(f'BOT ONLINE AND LISTENING FOR COMMANDS')
        
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
