# Tippy Bot - Troubleshooting Guide

## 🔍 Common Issues & Solutions

### Issue 1: "CoinGecko rate limited (429)" / API Rate Limiting Errors

**Symptoms:**
```
⏱️ CoinGecko rate limited (429)
⏱️ CoinMarketCap error: 429
⚠️ All APIs failed, using cached rate
```

**Root Cause:**
Too many API requests being sent too quickly to price APIs.

**Solution (ALREADY FIXED in v2.1):**
✅ Bot now has:
- 0.3-0.5 second delays between API calls
- Exponential backoff (30s → 60s → 120s → 300s)
- 20-minute caching to reduce API calls
- Session-based HTTP with automatic retries
- Better User-Agent headers

**Verification:**
```bash
# Should show backoff working
tail -f tippy_data/bot.log | grep "Backoff\|Exchange rate"
```

---

### Issue 2: "BlockCypher error" / API Connection Timeouts

**Symptoms:**
```
BlockCypher error for [ADDRESS]: 500
Connection timeout
[TIMEOUT] Deposit monitor timed out
```

**Root Cause:**
API timeout too short or BlockCypher API temporarily down.

**Solution (ALREADY FIXED in v2.1):**
✅ Updated timeouts:
- BlockCypher requests: 5s → 10-15s
- API calls: 5s → 8s
- Added timeout exception handling
- Retry logic for failed requests

**Verification:**
```bash
# Test BlockCypher directly
python -c "import requests; print(requests.get('https://api.blockcypher.com/v1/ltc/main', timeout=15).json())"
```

---

### Issue 3: "Deposit check complete - no new deposits"

**Symptoms:**
```
[CHECKING] Looking for deposits to sweep...
[OK] Deposit check complete
```

**Explanation:**
This is NORMAL! It means:
- The bot checked all deposit addresses
- No new deposits were detected (or already processed)
- Everything is working correctly

**Verification:**
```bash
# Check for actual deposits
grep "DEPOSIT DETECTED\|SWEEP" tippy_data/bot.log
```

---

### Issue 4: "urllib3 connectionpool" / Connection Pool Errors

**Symptoms:**
```
urllib3.exceptions.MaxRetryError
HTTPConnectionPool(host='api.coingecko.com')
Connection refused
```

**Root Cause:**
Network connectivity issues or API endpoint problems.

**Solution (ALREADY FIXED in v2.1):**
✅ Now handles:
- Connection errors gracefully
- Automatic fallback to next API
- Session-based retries
- Better error logging

**Verification:**
```bash
# Check network connectivity
ping api.coingecko.com
curl -I https://api.coingecko.com/api/v3/simple/price
```

---

### Issue 5: Bot Crashes on Startup

**Symptoms:**
```
Error loading commands
Fatal error
ImportError
```

**Solutions:**

**Check 1: Python Dependencies**
```bash
pip install -r requirements.txt
```

**Check 2: Environment Variables**
```bash
# Verify all required vars are set
python health_check.py
```

**Check 3: Import Errors**
```bash
# Test each module
python -c "import discord; print('discord.py OK')"
python -c "import bitcoinlib; print('bitcoinlib OK')"
python -c "import requests; print('requests OK')"
```

---

### Issue 6: "No available UTXOs" / Withdrawal Fails

**Symptoms:**
```
[TX] No available UTXOs at [ADDRESS]
[BROADCAST] ❌ BROADCAST FAILED
Insufficient funds
```

**Solutions:**

**For Users:**
1. Wait for deposit confirmations (6 blocks, ~10 min)
2. Check balance: `$balance`
3. Ensure withdrawal amount is valid

**For Bot:**
1. Check wallet has funds: https://blockchair.com/litecoin (search address)
2. Verify private key is correct
3. Check BlockCypher API key has rate limit

---

### Issue 7: Discord Bot Not Responding to Commands

**Symptoms:**
```
$deposit → no response
$balance → no response
Commands not being recognized
```

**Solutions:**

**Check 1: Bot Permissions**
- Go to Discord Server Settings → Roles
- Verify bot role has "Send Messages" permission
- Verify bot role has "Read Messages" permission

**Check 2: Bot Token**
```bash
# Verify token is correct
echo $DISCORD_TOKEN
```

**Check 3: Command Prefix**
- Bot uses `$` prefix
- Try: `$help` or `$deposit`
- Not `/` (that's slash commands, not implemented)

**Check 4: Bot Online Status**
```bash
# Check logs
tail -20 tippy_data/bot.log | grep "Bot ready"
```

---

### Issue 8: Exchange Rate Not Updating

**Symptoms:**
```
[RATE] Exchange rate updated: $0.00
Exchange rate is frozen
```

**Solutions:**

**Check 1: Clear Cache**
```bash
rm tippy_data/exchange_rate_cache.json
# Bot will fetch fresh rate on next refresh
```

**Check 2: Verify APIs**
```python
from exchange_rates import get_ltc_usd_rate
rate = get_ltc_usd_rate()
print(f"Rate: ${rate}")
```

**Check 3: Check Backoff Status**
```bash
grep "Backoff" tippy_data/bot.log
```

If backoff is active, wait for it to expire.

---

### Issue 9: High CPU Usage or Memory Leaks

**Symptoms:**
```
Bot using 100% CPU
Memory usage increasing over time
Bot becomes unresponsive
```

**Solutions:**

**Check 1: Review Logs for Loops**
```bash
# Check for infinite loops or stuck tasks
tail -100 tippy_data/bot.log | grep -i "loop\|error"
```

**Check 2: Restart Bot**
```bash
# Kill bot process
pkill -f bot_main.py

# Wait 5 seconds
sleep 5

# Restart
python bot_main.py
```

**Check 3: Monitor Resource Usage**
```bash
# Linux/Mac
watch -n 1 'ps aux | grep bot_main'

# Windows (PowerShell)
Get-Process python | Select ProcessName, CPU, Memory
```

---

### Issue 10: "DEPRECATED WARNING" Messages

**Symptoms:**
```
DeprecationWarning: ...
warnings.warn(...)
```

**Explanation:**
These are usually safe warnings from outdated library versions. They won't break the bot.

**Solution:**
Upgrade libraries:
```bash
pip install --upgrade discord.py bitcoinlib requests
```

---

## 🧪 Diagnostic Commands

### Check System Status
```bash
# Health check
python health_check.py

# Functionality tests
python test_functionality.py

# Startup check
python startup.py
```

### View Real-Time Activity
```bash
# Show all logs
tail -f tippy_data/bot.log

# Show only errors
tail -f tippy_data/bot.log | grep -i error

# Show only exchange rate updates
tail -f tippy_data/bot.log | grep "RATE"

# Show only deposits
tail -f tippy_data/bot.log | grep "DEPOSIT"

# Show only transactions
tail -f tippy_data/bot.log | grep "TX"
```

### Manual API Testing
```python
# Test exchange rate
python -c "from exchange_rates import get_ltc_usd_rate; print(f'Rate: ${get_ltc_usd_rate():.2f}')"

# Test BlockCypher
python -c "import requests; print(requests.get('https://api.blockcypher.com/v1/ltc/main', timeout=10).json())"

# Test user creation
python -c "from tippy_system import get_user_account; u=get_user_account(123); print(f'Address: {u.deposit_address}')"

# Test address validation
python -c "from address_validator import LitecoinValidator; print(LitecoinValidator.validate_address('LdG5p9gsPMNbwVwf2QXC3beFxCJYHmqv5p'))"
```

### Debug Mode
```bash
# Run with debug logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
exec(open('bot_main.py').read())
"
```

---

## 📊 Monitoring Checklist

Daily checks:
- [ ] Bot shows "Bot ready" in logs
- [ ] Exchange rate updating every 25 minutes
- [ ] No continuous error loops
- [ ] Memory usage stable
- [ ] CPU usage < 10% when idle

Weekly checks:
- [ ] User data file size reasonable
- [ ] No corrupted user data
- [ ] Deposit/withdrawal transactions working
- [ ] No security issues in logs

Monthly checks:
- [ ] BlockCypher API key still valid
- [ ] All dependencies up to date
- [ ] Full backup of user data
- [ ] Review error logs for patterns

---

## 🚨 Emergency Procedures

### Bot Stuck or Unresponsive

```bash
# Kill the process
pkill -9 -f bot_main.py

# Clear any temporary files
rm -f tippy_data/exchange_rate_cache.json

# Restart
python bot_main.py
```

### Corrupted User Data

```bash
# Backup current data
cp tippy_data/users.json tippy_data/users.json.backup

# Check file integrity
python -c "import json; json.load(open('tippy_data/users.json'))"

# If corrupted, restore from backup
cp tippy_data/users.json.backup tippy_data/users.json
```

### Lost Exchange Rate Cache

```bash
# Delete cache (will be recreated)
rm tippy_data/exchange_rate_cache.json

# Bot will fetch fresh rate automatically
```

---

## 📞 Getting Help

If you encounter issues not covered here:

1. **Check the logs first**
   ```bash
   tail -100 tippy_data/bot.log
   ```

2. **Run health check**
   ```bash
   python health_check.py
   ```

3. **Run functionality tests**
   ```bash
   python test_functionality.py
   ```

4. **Test individual components**
   - Use the diagnostic commands above
   - Check API endpoints manually
   - Verify environment variables

5. **Review error messages**
   - Most errors are descriptive
   - Check timestamps in logs
   - Look for patterns in errors

---

**Last Updated:** April 19, 2026
**Version:** 2.1 - Fully Functional with Enhanced Reliability
