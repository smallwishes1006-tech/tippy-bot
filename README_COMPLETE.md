# 🤖 TIPPY BOT - LITECOIN DISCORD TIPPING BOT

**Version:** 2.1 (Production Ready)  
**Status:** ✅ Fully Functional  
**Last Updated:** April 19, 2026

---

## ⚡ QUICK START

```bash
# 1. Verify everything is working
python health_check.py
python test_functionality.py

# 2. Start the bot
python startup.py
```

**OR directly:**
```bash
python bot_main.py
```

---

## 🎯 WHAT IS TIPPY BOT?

Tippy Bot is a Discord bot that enables users to:
- 💰 **Send Litecoin tips** to other Discord users instantly
- 💵 **Convert USD to LTC** automatically
- 📊 **Check real-time exchange rates**
- 🏦 **Deposit LTC** to their personal bot wallet
- 💸 **Withdraw LTC** to their own addresses
- ⛓️ **Track transaction confirmations** automatically

### Key Features
- **Custodial Wallet System** - Bot manages user funds securely
- **Real-time Price Fetching** - Multiple API fallbacks
- **Automatic Sweeping** - Deposits auto-sweep to master wallet
- **Transaction Monitoring** - Automatic confirmation tracking
- **Deposit Tracking** - Users see their balance and history
- **Rate Limiting** - Protection against spam and abuse
- **Rich Embeds** - Beautiful Discord interface

---

## 🚀 FEATURES & COMMANDS

### User Commands (Prefix: `$`)

| Command | Usage | Example |
|---------|-------|---------|
| `$deposit` | Get your deposit address | `$deposit` |
| `$balance` | Check balance and history | `$balance` |
| `$tip` | Tip a user | `$tip @alice 0.5$` |
| `$withdraw` | Withdraw to address | `$withdraw LTC_ADDR 0.1` |

### Command Examples

```
# Check your balance
$balance

# Get your deposit address
$deposit

# Tip someone 50 cents
$tip @alice 0.5$

# Tip someone your entire balance
$tip @bob all

# Withdraw 0.1 LTC to your wallet
$withdraw LdG5p9gsPMNbwVwf2QXC3beFxCJYHmqv5p 0.1

# Withdraw $25 worth of LTC
$withdraw LdG5p9gsPMNbwVwf2QXC3beFxCJYHmqv5p $25

# Withdraw your entire balance
$withdraw LdG5p9gsPMNbwVwf2QXC3beFxCJYHmqv5p all
```

---

## 📋 SETUP & DEPLOYMENT

### Requirements
- Python 3.8+
- Discord bot token
- Litecoin master wallet address & private key
- BlockCypher API key (optional, but recommended)

### Environment Variables (.env)

```bash
# REQUIRED
DISCORD_TOKEN=your_discord_bot_token_here
MASTER_WALLET_ADDRESS=your_litecoin_address_here
MASTER_WALLET_PRIVATE_KEY=your_private_key_wif_format_here

# OPTIONAL (but recommended)
BLOCKCYPHER_API_KEY=your_api_key_here
OWNER_DISCORD_ID=your_discord_user_id
OWNER_WALLET_ADDRESS=owner_litecoin_address

# OPTIONAL (with defaults)
MIN_TIP_AMOUNT=0.001
MAX_TIP_AMOUNT=100.0
```

### Installation

```bash
# Clone repository
git clone <repo-url>
cd tippy-bot-clean

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Run health check
python health_check.py

# Run functionality tests
python test_functionality.py

# Start bot
python bot_main.py
```

---

## 🏗️ ARCHITECTURE

### System Components

```
┌─────────────────────────────────────┐
│      Discord Bot (bot_main.py)      │
│  - Handles commands                 │
│  - Manages background tasks         │
│  - Logs all activity                │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        │             │
   ┌────▼───┐    ┌───▼────┐
   │Commands │    │Tasks   │
   │(tippy_  │    │(Deposit│
   │commands)│    │ Monitor)
   └────┬───┘    └───┬────┘
        │             │
   ┌────▼─────────────▼────┐
   │  Tippy System         │
   │  - User accounts      │
   │  - Transactions       │
   │  - Data persistence   │
   └────┬────────────┬─────┘
        │            │
   ┌────▼──┐    ┌───▼──────────┐
   │Users. │    │Exchange Rates│
   │json   │    │(CoinGecko,   │
   │       │    │ Binance...)  │
   └───────┘    └───┬──────────┘
                    │
            ┌───────┴──────────┐
            │                  │
      ┌─────▼───┐      ┌──────▼───┐
      │BlockCypher     │Litecoin  │
      │API (Mainnet)   │Network   │
      └──────────┘     └──────────┘
```

### Files & Responsibilities

| File | Purpose |
|------|---------|
| `bot_main.py` | Main bot entry point, background tasks |
| `tippy_commands.py` | Discord command handlers |
| `tippy_system.py` | User accounts, transactions, deposits |
| `exchange_rates.py` | Price fetching with fallbacks |
| `litecoin_signer.py` | Transaction signing and broadcasting |
| `address_validator.py` | Litecoin address validation |
| `config.py` | Configuration and environment vars |
| `health_check.py` | Pre-deployment verification |
| `test_functionality.py` | Feature testing |
| `startup.py` | Automated startup with checks |

---

## 📊 TECHNICAL DETAILS

### Exchange Rate System
- **4 Fallback APIs:** CoinGecko → CoinMarketCap → Binance → Kraken
- **Cache Duration:** 20 minutes (reduced for freshness)
- **Persistent Caching:** Survives bot restarts
- **Backoff Strategy:** 30s → 60s → 120s → 300s (max 5 min)
- **Rate Limit Protection:** 0.3-0.5s delays between calls
- **Error Recovery:** Exponential backoff with timeout handling

### Background Tasks
- **Deposit Monitor:** Every 5 minutes
  - Checks all deposit addresses
  - Detects new deposits after 6 confirmations
  - Sweeps to master wallet
  - Notifies users via DM

- **Exchange Rate Refresh:** Every 25 minutes
  - Fetches fresh price data
  - Updates cache
  - Handles rate limiting gracefully

- **TX Confirmation Monitor:** Every 2 minutes
  - Checks pending withdrawals
  - Updates status when confirmed
  - Notifies users when complete

### Transaction Flow

```
User Deposit:
1. User sends LTC to generated address
2. Bot detects unconfirmed transaction
3. After 6 confirmations, sweeps to master
4. Updates user balance
5. Notifies user via DM

User Withdrawal:
1. User initiates withdrawal in DM
2. Bot validates address
3. Creates transaction with BlockCypher
4. Signs with user's private key
5. Broadcasts to Litecoin network
6. Tracks pending TX
7. Updates status when confirmed
8. Notifies user
```

---

## 🔒 SECURITY FEATURES

1. **Key Management**
   - Private keys stored securely in `.env` (never in code)
   - User keys stored in encrypted JSON file
   - Master wallet key only used for sweeping

2. **Command Security**
   - Withdrawals only in DM (no public channel expose)
   - Address validation before any transaction
   - Rate limiting (5-minute cooldown per user)

3. **Data Protection**
   - Regular backups of `tippy_data/users.json`
   - Transaction history logged
   - Audit trail of all operations

4. **API Security**
   - No API keys hardcoded
   - Environment variables only
   - Proper error handling (no data leaks)

---

## 📈 MONITORING & LOGS

### Log Levels

```bash
# View all logs
tail -f tippy_data/bot.log

# View only errors
tail -f tippy_data/bot.log | grep ERROR

# View exchange rate updates
tail -f tippy_data/bot.log | grep RATE

# View deposits
tail -f tippy_data/bot.log | grep DEPOSIT

# View transactions
tail -f tippy_data/bot.log | grep TX

# View bot status
tail -f tippy_data/bot.log | grep "ready\|online"
```

### Important Log Entries

```
✅ Bot ready as TippyXXXX
✅ Tippy commands loaded
✅ Exchange rate updated: $XX.XX
✅ NEW DEPOSIT DETECTED: X.XXXXX LTC
✅ SWEEP SUCCESSFUL: [tx_hash]
✅ BROADCAST SUCCESSFUL: [tx_hash]
✅ TX [hash] confirmed!
```

---

## 🧪 TESTING & VALIDATION

### Health Check
Verifies all systems are operational:
```bash
python health_check.py
```

### Functionality Tests
Tests all features:
```bash
python test_functionality.py
```

### Startup Verification
Comprehensive pre-flight checks:
```bash
python startup.py
```

---

## 🐛 TROUBLESHOOTING

### Common Issues

**Bot won't start:**
```bash
python health_check.py  # Check configuration
python test_functionality.py  # Test dependencies
```

**No deposits detected:**
- Wait 6 confirmations (~10 minutes)
- Verify correct amount sent
- Check logs for errors

**Exchange rate not updating:**
- Check internet connection
- All APIs may be rate limited (wait 5 min)
- Check logs for backoff status

**Withdrawal fails:**
- Verify address is valid
- Ensure sufficient balance
- Check wallet has private key

For more details, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📚 DOCUMENTATION

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md)** - What was fixed in v2.1

---

## 🛠️ DEVELOPMENT

### Running in Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python bot_main.py
```

### Testing Individual Components
```python
# Test exchange rate
from exchange_rates import get_ltc_usd_rate
rate = get_ltc_usd_rate()
print(f"${rate:.2f}")

# Test user creation
from tippy_system import get_user_account
user = get_user_account(123456789)
print(user.deposit_address)

# Test address validation
from address_validator import LitecoinValidator
is_valid = LitecoinValidator.validate_address("LdG5...")
print(is_valid)
```

---

## 📦 DEPENDENCIES

- **discord.py** - Discord bot framework
- **requests** - HTTP library
- **bitcoinlib** - Litecoin key management
- **python-dotenv** - Environment variable loading
- **aiohttp** - Async HTTP (for Discord.py)

See [requirements.txt](requirements.txt) for full list.

---

## 📞 SUPPORT

### Getting Help

1. Check the logs: `tail -f tippy_data/bot.log`
2. Run health check: `python health_check.py`
3. Read troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. Review documentation: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Reporting Issues

Include:
- Full error message from logs
- Steps to reproduce
- Output from health check
- Discord bot status

---

## 📄 LICENSE

This project is provided as-is for educational and personal use.

---

## 🎉 YOU'RE READY!

Your Tippy Bot is:
- ✅ Fully functional
- ✅ Production ready
- ✅ Well documented
- ✅ Thoroughly tested

**Start the bot now:**
```bash
python startup.py
```

**Then test in Discord:**
- Use `$deposit` to get your address
- Use `$balance` to check balance
- Use `$tip` to send tips

Happy tipping! 💰

---

**Version:** 2.1  
**Last Updated:** April 19, 2026  
**Status:** ✅ Production Ready
