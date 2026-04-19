"""
Configuration and environment variables for Tippy Bot (Litecoin Custodial)
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# DISCORD CONFIGURATION
# ============================================================================
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = '$'
BOT_PREFIX = '/'  # Slash commands for new bot
ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')  # Parse comma-separated admin IDs
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '772300666458603520'))  # Discord user ID who owns the bot

# ============================================================================
# MONGODB CONFIGURATION
# ============================================================================
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DATABASE_NAME = 'tippy_bot'
DATABASE_USERS = 'users'
DATABASE_TRANSACTIONS = 'transactions'
DATABASE_DEPOSITS = 'deposits'

# ============================================================================
# BLOCKCYPHER API CONFIGURATION
# ============================================================================
# Bitcoin/Litecoin blockchain API (FREE tier)
# Get token: https://www.blockcypher.com/ 
# Free tier: 200 req/hour (sufficient for Discord bot)
BLOCKCYPHER_API_KEY = os.getenv('BLOCKCYPHER_API_KEY', '')  # Now required - no hardcoded key!
if not BLOCKCYPHER_API_KEY:
    import warnings
    warnings.warn("⚠️ BLOCKCYPHER_API_KEY not set! Using free tier limits. Set env var for higher limits.")


# ============================================================================
# BLOCKCHAIN CONFIGURATION
# ============================================================================
BLOCKCHAIN = 'LTC'  # Litecoin
NETWORK = 'mainnet'  # Production mainnet (real funds!)

# ============================================================================
# TIPPING CONFIGURATION
# ============================================================================
MIN_TIP_AMOUNT = float(os.getenv('MIN_TIP_AMOUNT', '0.001'))  # Min LTC to tip
MAX_TIP_AMOUNT = float(os.getenv('MAX_TIP_AMOUNT', '100.0'))  # Max LTC to tip
DECIMAL_PLACES = 8  # Litecoin has 8 decimal places

# ============================================================================
# WALLET & CUSTODY CONFIGURATION
# ============================================================================
MASTER_WALLET_ADDRESS = os.getenv('MASTER_WALLET_ADDRESS')  # Bot's master wallet
MASTER_WALLET_PRIVATE_KEY = os.getenv('MASTER_WALLET_PRIVATE_KEY')  # For signing withdrawals
DERIVATION_PATH = "m/44'/92'/0'/0"  # BIP44 path for Litecoin (coin type 92)
ADDRESS_GENERATION_TIMEOUT = 30  # seconds

# ============================================================================
# TRANSACTION & SECURITY
# ============================================================================
TRANSACTION_TIMEOUT = 300  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
CONFIRMATION_BLOCKS = 6  # Required confirmations for deposits

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = 'tippy_bot.log'

# ============================================================================
# VALIDATION
# ============================================================================
# Minimum balance to prevent dust
MINIMUM_WALLET_BALANCE = 0.0001  # LTC

# Fee structure for withdrawals (NEW: Fixed fees in cents USD)
# Platform fee: 1 cent ($0.01) to owner's wallet
WITHDRAWAL_FEE_CENTS = float(os.getenv('WITHDRAWAL_FEE_CENTS', '1.0'))  # 1 cent USD

# Minimum withdrawal: 2 cents ($0.02) - converted to LTC at market rate
MIN_WITHDRAWAL_CENTS = float(os.getenv('MIN_WITHDRAWAL_CENTS', '2.0'))  # 2 cents USD

# Network fee is fetched from BlockCypher (market rate) - no fixed fee
# Will be deducted based on current Litecoin network congestion

OWNER_WALLET_ADDRESS = os.getenv('OWNER_WALLET_ADDRESS')  # Blockchain address for withdrawals
# Owner's Discord ID for fee credits
_owner_id_str = os.getenv('OWNER_DISCORD_ID', '').strip()
OWNER_DISCORD_ID = int(_owner_id_str) if _owner_id_str and _owner_id_str.isdigit() else None

# ============================================================================
# MARKET RATE CONFIGURATION
# ============================================================================
# For converting USD fees to LTC (will update from CoinGecko API)
LTC_PRICE_USD = float(os.getenv('LTC_PRICE_USD', '0'))  # Updated periodically

# ============================================================================
# MAGIC NUMBERS - MOVED FROM HARDCODED VALUES
# ============================================================================

# BlockCypher API timeouts (seconds)
BLOCKCYPHER_TIMEOUT_BALANCE = int(os.getenv('BLOCKCYPHER_TIMEOUT_BALANCE', '10'))
BLOCKCYPHER_TIMEOUT_BROADCAST = int(os.getenv('BLOCKCYPHER_TIMEOUT_BROADCAST', '15'))
BLOCKCYPHER_TIMEOUT_TX_STATUS = int(os.getenv('BLOCKCYPHER_TIMEOUT_TX_STATUS', '10'))

# Transaction size estimation (bytes)
ESTIMATED_TX_SIZE_BYTES = int(os.getenv('ESTIMATED_TX_SIZE_BYTES', '300'))

# Fee calculation constants
FEE_PER_KB_LOW = int(os.getenv('FEE_PER_KB_LOW', '1000'))  # satoshis per KB (low priority)
FEE_PER_KB_MEDIUM = int(os.getenv('FEE_PER_KB_MEDIUM', '2000'))  # satoshis per KB (medium)
FEE_PER_KB_HIGH = int(os.getenv('FEE_PER_KB_HIGH', '3000'))  # satoshis per KB (high)
FEE_PER_KB_CURRENT = FEE_PER_KB_LOW  # Default to low for cost savings

# Dust limit (minimum unspent output value)
DUST_LIMIT = int(os.getenv('DUST_LIMIT', '546'))  # satoshis

# Background task timings
MONITOR_DEPOSITS_INTERVAL_MINUTES = int(os.getenv('MONITOR_DEPOSITS_INTERVAL_MINUTES', '5'))
MONITOR_PENDING_TXS_INTERVAL_MINUTES = int(os.getenv('MONITOR_PENDING_TXS_INTERVAL_MINUTES', '2'))
REFRESH_EXCHANGE_RATE_INTERVAL_MINUTES = int(os.getenv('REFRESH_EXCHANGE_RATE_INTERVAL_MINUTES', '25'))

# Transaction confirmation requirements
REQUIRED_CONFIRMATIONS_DEPOSIT = int(os.getenv('REQUIRED_CONFIRMATIONS_DEPOSIT', '6'))
REQUIRED_CONFIRMATIONS_SWEEP = int(os.getenv('REQUIRED_CONFIRMATIONS_SWEEP', '1'))

# Pending transaction expiration (seconds)
PENDING_TX_EXPIRATION_SECONDS = int(os.getenv('PENDING_TX_EXPIRATION_SECONDS', '86400'))  # 24 hours

# Rate limiting for commands
COMMAND_COOLDOWN_SECONDS = int(os.getenv('COMMAND_COOLDOWN_SECONDS', '5'))
BALANCE_CHECK_COOLDOWN_SECONDS = int(os.getenv('BALANCE_CHECK_COOLDOWN_SECONDS', '2'))
WITHDRAWAL_COOLDOWN_SECONDS = int(os.getenv('WITHDRAWAL_COOLDOWN_SECONDS', '30'))

# Exchange rate cache duration
EXCHANGE_RATE_CACHE_SECONDS = int(os.getenv('EXCHANGE_RATE_CACHE_SECONDS', '1200'))  # 20 minutes

# Validation
WITHDRAWAL_AMOUNT_PRECISION = 8  # Decimal places for amounts
MAX_ADDRESS_LENGTH = 100  # Litecoin address max length for validation
MIN_ADDRESS_LENGTH = 26  # Litecoin address min length for validation
