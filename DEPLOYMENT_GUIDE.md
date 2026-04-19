# Tippy Bot - PRODUCTION DEPLOYMENT GUIDE

**Version:** 2.1 - Production Ready
**Last Updated:** April 19, 2026
**Status:** ✅ FULLY FUNCTIONAL

---

## 📋 MAJOR IMPROVEMENTS IN THIS VERSION

### 🔧 Critical Fixes

1. **Exchange Rate API Reliability**
   - Added intelligent retry logic with exponential backoff
   - Implemented rate limit protection with request delays
   - Enhanced User-Agent headers to avoid API blocks
   - Switched to session-based HTTP with automatic retries
   - Now tries 4 different APIs in sequence (CoinGecko → CoinMarketCap → Binance → Kraken)
   - Improved caching mechanism with disk persistence

2. **API Request Handling**
   - Added 0.3-0.5s delays between API calls to prevent rate limiting
   - Increased timeout from 5s to 8s for more reliable connections
   - Added proper timeout exception handling
   - Implemented retry logic for failed requests (up to 3 attempts)

3. **Transaction Broadcasting**
   - Added 3-attempt retry loop for broadcast failures
   - Implemented connection error recovery
   - Better timeout handling for blockchain submissions

4. **Bot Stability**
   - Improved error handling in all background tasks
   - Added timeout exception handling for async operations
   - Better logging for debugging issues

5. **Security Improvements**
   - Removed hardcoded BlockCypher API key from config
   - Now requires environment variable (with warning if not set)
   - Better error messages without exposing sensitive data

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Environment Setup

```bash
# Create .env file with all required variables
# (See .env.example or below for required vars)

DISCORD_TOKEN=your_discord_bot_token_here
MASTER_WALLET_ADDRESS=your_litecoin_address
MASTER_WALLET_PRIVATE_KEY=your_private_key_in_wif_format

# Optional but recommended
BLOCKCYPHER_API_KEY=your_blockcypher_api_key
OWNER_DISCORD_ID=your_discord_user_id
OWNER_WALLET_ADDRESS=owner_litecoin_address
```

### Step 2: Health Check

```bash
python health_check.py
```

Expected output:
```
✅ PASS: Environment Variables
✅ PASS: Python Dependencies
✅ PASS: Data Directory
✅ PASS: Wallet Configuration
✅ PASS: Exchange Rate API
```

### Step 3: Functionality Test

```bash
python test_functionality.py
```

This will verify:
- Exchange rate fetching
- Address validation
- BlockCypher API connectivity
- User account creation

### Step 4: Start Bot

```bash
# Production mode
python bot_main.py

# Or with nohup (for server/VPS)
nohup python bot_main.py > logs/bot.log 2>&1 &

# Or with systemd (Linux)
systemctl start tippy-bot
```

---

## 🔍 MONITORING & TROUBLESHOOTING

### Check Bot Status

```bash
# View real-time logs
tail -f tippy_data/bot.log

# Check for errors in last 50 lines
tail -50 tippy_data/bot.log | grep -i error

# Monitor exchange rate updates
tail -f tippy_data/bot.log | grep "RATE"

# Monitor deposits
tail -f tippy_data/bot.log | grep "DEPOSIT"
```

### Common Issues & Solutions

#### Issue: "⏱️ CoinGecko rate limited (429)"
- **Cause**: Too many API requests in short time
- **Solution**: Already fixed! Bot now has 0.3-0.5s delays and caching
- **Check**: Exchange rate will use cached value with automatic backoff

#### Issue: "Deposit monitor error"
- **Cause**: BlockCypher API timeout
- **Solution**: Timeout increased from 5s to 15s. Bot will retry next cycle
- **Check**: Logs show "[TIMEOUT] Deposit monitor timed out"

#### Issue: "Transaction broadcast failed"
- **Cause**: Network issue or blockchain congestion
- **Solution**: Bot now retries up to 3 times automatically
- **Check**: Look for "[TX]" messages in logs

#### Issue: "BLOCKCYPHER_API_KEY not set"
- **Cause**: Environment variable not configured
- **Solution**: 
  - Set `BLOCKCYPHER_API_KEY` in `.env` for higher rate limits
  - Or use free tier (200 requests/hour should be enough)
- **Check**: `python health_check.py` will warn you

---

## 📊 COMMAND REFERENCE

### User Commands (Prefix: $)

```
$deposit          - Get your deposit address and balance
$balance          - Check current balance and transaction history
$tip @user 0.5$   - Tip a user (amount in USD)
$tip @user all    - Tip all your balance
$withdraw ADDRESS 0.1        - Withdraw LTC (amount in LTC)
$withdraw ADDRESS $50        - Withdraw USD (converted to LTC)
$withdraw ADDRESS all        - Withdraw entire balance
```

### Important Notes:
- **Deposits**: Require 6 confirmations (~10 minutes)
- **Withdrawals**: Only work in DM for security
- **Rate Limit**: 5-minute cooldown between withdrawals per user
- **Fees**: 
  - Service fee: $0.01 USD
  - Network fee: Automatic (market-based)
  - Minimum withdrawal: $0.02 USD

---

## 🔒 SECURITY BEST PRACTICES

1. **Private Keys**: Never commit `.env` file to git
2. **API Keys**: Rotate BlockCypher keys periodically
3. **Bot Token**: Keep Discord token secret
4. **Backups**: Regular backups of `tippy_data/users.json`
5. **Monitoring**: Check logs regularly for suspicious activity

---

## 📈 PERFORMANCE METRICS

### Background Tasks
- **Deposit Monitor**: Every 5 minutes
- **Exchange Rate Refresh**: Every 25 minutes
- **TX Confirmation Check**: Every 2 minutes

### API Rate Limits
- **BlockCypher**: 200 req/hour (free tier)
- **CoinGecko**: ~10-50 req/minute
- **Binance**: 1200 req/minute
- **Kraken**: 15 req/second

### Caching Strategy
- **Exchange Rate**: 20-minute cache (reduced for freshness)
- **Disk Persistence**: Survives bot restarts
- **Smart Backoff**: 30s → 60s → 120s → 300s max

---

## 🚨 ALERT INDICATORS

### Good Signs ✅
```
[OK] Bot ready as TippyXXXX
[OK] Tippy commands loaded
✅ Exchange rate updated: $XX.XX
[OK] Deposit check complete
```

### Warning Signs ⚠️
```
⏱️ Backoff active (60s), using cached: $XX.XX
[WAIT] Rate Limited
⚠️ All APIs failed, using cached rate
```

### Error Signs ❌
```
[ERROR] Error in on_ready
❌ Withdrawal error
[BROADCAST] ❌ BROADCAST FAILED
Missing environment variable
```

---

## 📞 SUPPORT & DEBUGGING

### Enable Debug Logging
```python
# In bot_main.py, change logging level
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    ...
)
```

### Clear Cache if Needed
```bash
rm tippy_data/exchange_rate_cache.json
```

### Test Exchange Rate Manually
```python
from exchange_rates import get_ltc_usd_rate
rate = get_ltc_usd_rate()
print(f"Current rate: ${rate:.2f}")
```

### Reset User Data
```python
import json
import os
os.remove('tippy_data/users.json')  # Careful - this deletes all user data!
```

---

## 📦 DEPLOYMENT CHECKLIST

Before going to production:

- [ ] All environment variables set in `.env`
- [ ] `python health_check.py` shows all ✅
- [ ] `python test_functionality.py` passes all tests
- [ ] Bot token works (can connect to Discord)
- [ ] Master wallet address is correct and funded
- [ ] BlockCypher API key obtained (optional but recommended)
- [ ] `.env` file added to `.gitignore`
- [ ] Regular backup process in place
- [ ] Monitoring/alerting setup (optional)
- [ ] Discord permissions configured correctly

---

## 🎯 NEXT STEPS

1. **Run health check**: `python health_check.py`
2. **Run functionality tests**: `python test_functionality.py`
3. **Start bot**: `python bot_main.py`
4. **Monitor logs**: `tail -f tippy_data/bot.log`
5. **Test commands**: Use `$deposit` and `$balance` in Discord

---

## 📝 VERSION HISTORY

### v2.1 (Current)
- ✅ Fixed all API rate limiting issues
- ✅ Added intelligent retry logic
- ✅ Improved error handling
- ✅ Enhanced timeout handling
- ✅ Security improvements

### v2.0
- Added deposit monitoring
- Added transaction confirmation tracking
- Implemented withdrawal feature

### v1.0
- Initial release
- Basic tipping functionality

---

**🎉 Your Tippy Bot is now FULLY FUNCTIONAL and PRODUCTION READY! 🎉**
