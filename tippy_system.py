"""
Core Tippy system - user accounts and transactions
"""

import json
import os
import logging
import discord
import time
from dataclasses import dataclass, asdict
from bitcoinlib.keys import Key
from litecoin_signer import LitecoinSigner
import config

logger = logging.getLogger('tippy_system')

DATA_FILE = 'tippy_data/users.json'


class RateLimiter:
    """Simple rate limiter for API calls (prevents BlockCypher free tier exhaustion)"""
    
    def __init__(self, max_calls: int, time_window_seconds: int):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Max calls allowed in time window
            time_window_seconds: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window_seconds
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Check if a call is allowed"""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # Check if we have room for another call
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_if_needed(self):
        """Wait if needed before making another call"""
        if not self.is_allowed():
            now = time.time()
            oldest_call = self.calls[0]
            wait_time = (oldest_call + self.time_window) - now
            if wait_time > 0:
                logger.warning(f"[RATE_LIMIT] Waiting {wait_time:.1f}s to respect rate limits")
                time.sleep(wait_time)
                self.calls = [call_time for call_time in self.calls if time.time() - call_time < self.time_window]


# BlockCypher rate limiter (200 req/hour = ~3.3 req/min)
# Conservative: 2 req/min (120 req/hour) with burst allowance
BLOCKCYPHER_RATE_LIMITER = RateLimiter(max_calls=2, time_window_seconds=60)


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
    """Save all users to database with atomic write and backup"""
    import shutil
    import tempfile
    
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    # Create backup if file exists
    if os.path.exists(DATA_FILE):
        backup_file = f"{DATA_FILE}.backup"
        try:
            shutil.copy2(DATA_FILE, backup_file)
            logger.debug(f"Backup created: {backup_file}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    # Write to temporary file first (atomic operation)
    temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(DATA_FILE), suffix='.tmp')
    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(users, f, indent=2)
        
        # Atomic rename (fails if can't write, doesn't corrupt existing file)
        os.replace(temp_path, DATA_FILE)
        logger.debug(f"Database saved atomically: {DATA_FILE}")
    except Exception as e:
        logger.error(f"Failed to save database: {e}", exc_info=True)
        # Clean up temp file if rename failed
        try:
            os.unlink(temp_path)
        except:
            pass
        raise


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
        logger.info(f"[BROADCAST] 📤 Withdrawal request: {amount_ltc:.8f} LTC from {from_address[:20]}... to {to_address[:20]}...")
        
        # Determine the private key
        found_key = None
        
        # Check if this is the master wallet
        if from_address == config.MASTER_WALLET_ADDRESS:
            found_key = config.MASTER_WALLET_PRIVATE_KEY
            logger.debug(f"[BROADCAST] Using master wallet key")
        else:
            # Try to find the key in our database
            logger.debug(f"[BROADCAST] Looking up private key in database...")
            all_users = load_all_users()
            for user_data in all_users.values():
                if user_data.get('deposit_address') == from_address:
                    found_key = user_data.get('deposit_key')
                    logger.debug(f"[BROADCAST] Found key in database")
                    break
        
        if not found_key:
            logger.error(f"[BROADCAST] ❌ Private key not found for {from_address}")
            return None
        
        # Use LitecoinSigner to create and broadcast
        logger.info(f"[BROADCAST] ✅ Starting transaction creation...")
        tx_hash = LitecoinSigner.withdraw(
            from_address=from_address,
            to_address=to_address,
            amount=amount_ltc,
            private_key_wif=found_key,
            use_rbf=True
        )
        
        if tx_hash:
            logger.info(f"[BROADCAST] ✅ BROADCAST SUCCESSFUL: {tx_hash}")
        else:
            logger.error(f"[BROADCAST] ❌ BROADCAST FAILED: Could not create/broadcast transaction")
        
        return tx_hash
        
    except Exception as e:
        logger.error(f"[BROADCAST] ❌ Withdrawal error: {e}", exc_info=True)
        return None


async def check_deposits(bot=None):
    """
    Check for new deposits and sweep them to master wallet
    Only sweeps when balance changes (confirmed deposits)
    Optionally notifies user via Discord DM if bot is provided
    """
    try:
        all_users = load_all_users()
        sweep_count = 0
        
        for user_id, user_data in all_users.items():
            deposit_addr = user_data.get('deposit_address')
            deposit_key = user_data.get('deposit_key')
            current_balance = user_data.get('balance', 0)
            user_id_int = int(user_id)
            
            if not deposit_addr or not deposit_key:
                continue
            
            # Check balance at this address
            logger.debug(f"[DEPOSIT CHECK] Checking {deposit_addr} (current balance: {current_balance:.8f} LTC)")
            
            try:
                import requests
                # Get balance from BlockCypher
                url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{deposit_addr}/full"
                resp = requests.get(url, params={"token": config.BLOCKCYPHER_API_KEY or ""}, timeout=15)
                
                if resp.status_code != 200:
                    logger.warning(f"[DEPOSIT CHECK] BlockCypher error for {deposit_addr}: {resp.status_code}")
                    continue
                
                data = resp.json()
                # Use final_balance (confirmed only)
                balance_satoshis = data.get('final_balance', 0)
                
                if balance_satoshis <= 0:
                    logger.debug(f"[DEPOSIT CHECK] No confirmed balance at {deposit_addr}")
                    continue  # No confirmed deposits
                
                balance_ltc = balance_satoshis / 1e8
                
                # Only sweep if there's NEW confirmed balance (more than we already counted)
                if balance_ltc > current_balance:
                    new_deposit = balance_ltc - current_balance
                    logger.info(f"[DEPOSIT] ✅ NEW DEPOSIT DETECTED: {new_deposit:.8f} LTC at {deposit_addr}")
                    logger.info(f"[DEPOSIT]    Blockchain Balance: {balance_ltc:.8f} LTC | Stored Balance: {current_balance:.8f} LTC")
                    
                    # Sweep all confirmed funds to master wallet
                    logger.info(f"[SWEEP] 🔄 Starting sweep of {balance_ltc:.8f} LTC to {config.MASTER_WALLET_ADDRESS}...")
                    
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
                        
                        # Track in pending transactions
                        if user.pending_txs is None:
                            user.pending_txs = []
                        user.pending_txs.append(tx_hash)
                        
                        # Add to withdrawal history for tracking
                        if user.withdrawal_history is None:
                            user.withdrawal_history = []
                        
                        import time
                        user.withdrawal_history.append({
                            "tx_hash": tx_hash,
                            "amount": balance_ltc,
                            "address": config.MASTER_WALLET_ADDRESS,
                            "time": time.time(),
                            "status": "pending",
                            "type": "sweep"
                        })
                        
                        user.save()
                        sweep_count += 1
                        logger.info(f"[SWEEP] ✅ SUCCESS: {balance_ltc:.8f} LTC swept. TX: {tx_hash}")
                        logger.info(f"[SWEEP]    New balance in database: {user.balance:.8f} LTC")
                    else:
                        logger.error(f"[SWEEP] ❌ FAILED: sweep_to_master returned None for {deposit_addr}")
                        logger.error(f"[SWEEP]    Amount: {balance_ltc:.8f} LTC")
                        logger.error(f"[SWEEP]    Check litecoin_signer logs above for error details")
                    
            except Exception as e:
                logger.error(f"[DEPOSIT CHECK] ❌ Error checking {deposit_addr}: {e}", exc_info=True)
        
        if sweep_count > 0:
            logger.info(f"[DEPOSIT] ✅ Deposit check complete - {sweep_count} sweep(s) processed")
        else:
            logger.debug(f"[DEPOSIT] Deposit check complete - no new deposits")
        
    except Exception as e:
        logger.error(f"[DEPOSIT CHECK] ❌ Fatal error: {e}", exc_info=True)


def broadcast_withdrawal(from_address: str, to_address: str, amount_ltc: float) -> str:
    """
    Broadcast a withdrawal transaction to the blockchain
    CRITICAL: Validates broadcast success before returning hash
    
    Args:
        from_address: Master wallet address (where funds are swept)
        to_address: User's external address
        amount_ltc: Amount in LTC to send
    
    Returns:
        Transaction hash if successful, None otherwise
    """
    try:
        logger.info(f"[BROADCAST] 📤 Withdrawal: {amount_ltc:.8f} LTC to {to_address[:20]}...")
        
        # Get the master wallet's private key
        if not config.MASTER_WALLET_PRIVATE_KEY:
            logger.error("[BROADCAST] ❌ MASTER_WALLET_PRIVATE_KEY not configured")
            return None
        
        # Use LitecoinSigner to create and broadcast the transaction
        from litecoin_signer import LitecoinSigner
        
        # Make the withdrawal
        tx_hash = LitecoinSigner.withdraw(
            from_address=from_address,
            to_address=to_address,
            amount=amount_ltc,
            private_key_wif=config.MASTER_WALLET_PRIVATE_KEY,
            use_rbf=True
        )
        
        if not tx_hash:
            logger.error("[BROADCAST] ❌ Transaction creation failed - LitecoinSigner returned None")
            return None
        
        # Validate the TX hash format (should be 64 hex characters)
        if not isinstance(tx_hash, str) or len(tx_hash) != 64:
            logger.error(f"[BROADCAST] ❌ Invalid TX hash format: {tx_hash}")
            return None
        
        logger.info(f"[BROADCAST] ✅ Transaction broadcast successful: {tx_hash[:20]}...")
        return tx_hash
        
    except Exception as e:
        logger.error(f"[BROADCAST] ❌ Broadcast error: {e}", exc_info=True)
        return None
