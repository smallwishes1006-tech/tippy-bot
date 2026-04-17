"""
Core Tippy system - user accounts and transactions
"""

import json
import os
import logging
import discord
from dataclasses import dataclass, asdict
from bitcoinlib.keys import Key
from litecoin_signer import LitecoinSigner
import config

logger = logging.getLogger('tippy_system')

DATA_FILE = 'tippy_data/users.json'


@dataclass
class UserAccount:
    """User account data"""
    user_id: int
    username: str = ""
    balance: float = 0.0
    deposit_address: str = ""
    deposit_key: str = ""
    total_received: float = 0.0
    total_sent: float = 0.0
    confirmed_balance: float = 0.0  # Confirmed deposits only
    unconfirmed_balance: float = 0.0  # Pending deposits
    last_withdrawal_time: float = 0.0  # Timestamp of last withdrawal (rate limiting)
    withdrawal_history: list = None  # List of {tx_hash, amount, address, time, status}
    pending_txs: list = None  # List of pending transaction hashes
    
    def __post_init__(self):
        """Initialize mutable defaults"""
        if self.withdrawal_history is None:
            self.withdrawal_history = []
        if self.pending_txs is None:
            self.pending_txs = []
    
    def save(self):
        """Save to database"""
        all_users = load_all_users()
        all_users[str(self.user_id)] = asdict(self)
        save_all_users(all_users)
        logger.debug(f"Saved user {self.user_id}")


def load_all_users() -> dict:
    """Load all users from database"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_all_users(users: dict):
    """Save all users to database"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def log_withdrawal(user_id: int, tx_hash: str, amount_ltc: float, to_address: str, status: str = "pending"):
    """Log withdrawal to user's history"""
    import time
    user = get_user_account(user_id)
    
    if user.withdrawal_history is None:
        user.withdrawal_history = []
    if user.pending_txs is None:
        user.pending_txs = []
    
    # Add to history
    user.withdrawal_history.append({
        "tx_hash": tx_hash,
        "amount": amount_ltc,
        "address": to_address,
        "time": time.time(),
        "status": status
    })
    
    # Add to pending if not confirmed
    if status == "pending" and tx_hash not in user.pending_txs:
        user.pending_txs.append(tx_hash)
    
    user.last_withdrawal_time = time.time()
    user.save()
    logger.info(f"Logged withdrawal for user {user_id}: {tx_hash} ({status})")


def get_user_account(user_id: int, username: str = "") -> UserAccount:
    """Get or create user account"""
    all_users = load_all_users()
    
    if str(user_id) in all_users:
        data = all_users[str(user_id)]
        
        # Handle missing new fields from old accounts
        if 'last_withdrawal_time' not in data:
            data['last_withdrawal_time'] = 0.0
        if 'withdrawal_history' not in data:
            data['withdrawal_history'] = []
        if 'pending_txs' not in data:
            data['pending_txs'] = []
        if 'confirmed_balance' not in data:
            data['confirmed_balance'] = data.get('balance', 0.0)
        if 'unconfirmed_balance' not in data:
            data['unconfirmed_balance'] = 0.0
        
        return UserAccount(**data)
    
    # Create new account
    key = Key(network='litecoin')
    deposit_address = key.address()
    deposit_key = key.wif()
    
    user = UserAccount(
        user_id=user_id,
        username=username,
        balance=0.0,
        deposit_address=deposit_address,
        deposit_key=deposit_key,
        total_received=0.0,
        total_sent=0.0
    )
    
    user.save()
    logger.info(f"✅ Created account for user {user_id}")
    logger.debug(f"   Address: {deposit_address}")
    
    return user


def broadcast_withdrawal(from_address: str, to_address: str, amount_ltc: float) -> str:
    """
    Broadcast a withdrawal transaction to the blockchain
    Returns transaction hash or None
    Note: Service fee is just a database deduction (not sent on-chain)
    """
    try:
        logger.info(f"Broadcasting: {amount_ltc} LTC from {from_address} to {to_address}")
        
        # Determine the private key
        found_key = None
        
        # Check if this is the master wallet
        if from_address == config.MASTER_WALLET_ADDRESS:
            found_key = config.MASTER_WALLET_PRIVATE_KEY
            logger.info(f"Using master wallet private key")
        else:
            # Try to find the key in our database
            all_users = load_all_users()
            for user_data in all_users.values():
                if user_data.get('deposit_address') == from_address:
                    found_key = user_data.get('deposit_key')
                    break
        
        if not found_key:
            logger.error(f"Private key not found for {from_address}")
            return None
        
        # Use LitecoinSigner to create and broadcast
        tx_hash = LitecoinSigner.withdraw(
            from_address=from_address,
            to_address=to_address,
            amount=amount_ltc,
            private_key_wif=found_key,
            use_rbf=True
        )
        
        if tx_hash:
            logger.info(f"✅ Broadcast successful: {tx_hash}")
        else:
            logger.error(f"❌ Broadcast failed")
        
        return tx_hash
        
    except Exception as e:
        logger.error(f"Withdrawal error: {e}", exc_info=True)
        return None


async def check_deposits(bot=None):
    """
    Check for new deposits and sweep them to master wallet
    Only sweeps when balance changes (confirmed deposits)
    Optionally notifies user via Discord DM if bot is provided
    """
    try:
        all_users = load_all_users()
        
        for user_id, user_data in all_users.items():
            deposit_addr = user_data.get('deposit_address')
            deposit_key = user_data.get('deposit_key')
            current_balance = user_data.get('balance', 0)
            user_id_int = int(user_id)
            
            if not deposit_addr or not deposit_key:
                continue
            
            # Check balance at this address
            logger.debug(f"Checking deposits for {deposit_addr}")
            
            try:
                import requests
                # Get balance from BlockCypher
                url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{deposit_addr}/full"
                resp = requests.get(url, params={"token": config.BLOCKCYPHER_API_KEY or ""}, timeout=10)
                
                if resp.status_code != 200:
                    logger.warning(f"BlockCypher error for {deposit_addr}: {resp.status_code}")
                    continue
                
                data = resp.json()
                # Use final_balance (confirmed only)
                balance_satoshis = data.get('final_balance', 0)
                
                if balance_satoshis <= 0:
                    continue  # No confirmed deposits
                
                balance_ltc = balance_satoshis / 1e8
                
                # Only sweep if there's NEW confirmed balance (more than we already counted)
                if balance_ltc > current_balance:
                    new_deposit = balance_ltc - current_balance
                    logger.info(f"[DEPOSIT] New confirmed deposit: {new_deposit:.8f} LTC at {deposit_addr}")
                    
                    # Sweep all confirmed funds to master wallet
                    logger.info(f"[SWEEP] Sweeping {balance_ltc:.8f} LTC to master wallet...")
                    
                    from litecoin_signer import LitecoinSigner
                    tx_hash = LitecoinSigner.sweep_to_master(
                        from_address=deposit_addr,
                        private_key_wif=deposit_key,
                        amount_ltc=balance_ltc
                    )
                    
                    if tx_hash:
                        # Update user balance to final confirmed amount
                        user = UserAccount(**user_data)
                        user.balance = balance_ltc
                        user.total_received += new_deposit
                        user.save()
                        logger.info(f"[OK] Swept {balance_ltc:.8f} LTC for user {user_id}. New balance: {user.balance:.8f}")
                        
                        # Send DM notification if bot provided
                        if bot:
                            try:
                                user_discord = await bot.fetch_user(user_id_int)
                                embed = discord.Embed(
                                    title="Deposit Received!",
                                    description=f"New deposit: **{new_deposit:.8f} LTC** (~${new_deposit * 50:.2f})",
                                    color=discord.Color.green()
                                )
                                embed.add_field(name="Your Balance", value=f"**{balance_ltc:.8f} LTC**", inline=False)
                                embed.add_field(name="TX", value=f"`{tx_hash[:30]}...`", inline=False)
                                embed.set_footer(text="Sweep to master wallet confirmed")
                                await user_discord.send(embed=embed)
                            except Exception as e:
                                logger.debug(f"Could not notify user {user_id}: {e}")
                    else:
                        logger.warning(f"[FAIL] Sweep failed for {deposit_addr}")
                    
            except Exception as e:
                logger.warning(f"Deposit check error for {deposit_addr}: {e}")
            
    except Exception as e:
        logger.error(f"Deposit check error: {e}")
