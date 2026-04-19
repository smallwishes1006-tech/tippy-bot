# 🔄 BULK SWEEP GUIDE

## Overview

The `bulk_sweep.py` script consolidates all funds from every user's deposit address to your master wallet.

This is useful for:
- ✅ Consolidating funds after many users have deposited
- ✅ Centralizing all customer funds in master wallet
- ✅ Recovering funds from old/abandoned addresses
- ✅ Periodic account reconciliation

---

## How to Use

### Step 1: DRY RUN (No Real Transactions)

First, preview what would be swept WITHOUT executing:

```powershell
cd C:\Users\small\tippy-bot-clean
python bulk_sweep.py
```

**Output:**
```
======================================================================
BULK SWEEP - DRY RUN
======================================================================

📊 Found 3 users with funds to sweep

User 123456789:
  Address: LYGpJXkCvVrAhR1T7qnVr...
  Confirmed: 0.05000000 LTC
  Unconfirmed: 0.01000000 LTC
  Total: 0.06000000 LTC
  ✅ Swept 0.05000000 LTC
  TX: DRY RUN

======================================================================
SWEEP SUMMARY
======================================================================
Total Users: 3
Users with Balance: 3
Successful Sweeps: 3
Failed Sweeps: 0
Total Amount Swept: 0.15000000 LTC
Master Wallet: LgtpifMGDFirYSp39esx3zb4v47KgqubBk
======================================================================

✅ Successfully swept 0.15000000 LTC to master wallet!
```

---

### Step 2: Execute Live Sweep

Once you're confident with the dry run, execute for real:

```powershell
python bulk_sweep.py --execute
```

**Warning prompt:**
```
⚠️  WARNING: LIVE EXECUTION MODE
This will broadcast real transactions to Litecoin mainnet!
Master wallet: LgtpifMGDFirYSp39esx3zb4v47KgqubBk

Type 'YES' to confirm:
```

Type `YES` to execute, or anything else to cancel.

---

## Features

### ✅ Safe Operations

1. **Validates all addresses** before sweeping
2. **Only sweeps confirmed balance** (ignores unconfirmed)
3. **Prevents typos** with address validation
4. **Dry-run by default** (must add `--execute` flag for real)
5. **Rate limiting** to avoid API errors
6. **Complete logging** to `tippy_data/sweep.log`

### ✅ Smart Handling

- Skips users with no balance
- Detects confirmed vs unconfirmed
- Only sweeps confirmed (safe from double-spend)
- Calculates dynamic network fees
- Generates transaction history
- Saves results to JSON

### ✅ Detailed Reporting

**Console output:**
- Each user's address and balance
- Sweep success/failure status
- Transaction hashes
- Summary with totals

**Log file:** `tippy_data/sweep.log`
- Detailed debug info
- Error messages
- Timestamps

**Results file:** `tippy_data/sweep_results.json`
- Machine-readable results
- Can be used for reconciliation

---

## Command Options

### Dry Run (Default - Safe)
```powershell
python bulk_sweep.py
```
Shows what would happen, doesn't broadcast.

### Execute Live
```powershell
python bulk_sweep.py --execute
```
Actually broadcasts to blockchain. **Requires confirmation.**

### Sweep Specific Users Only
```powershell
python bulk_sweep.py --execute --users 123456789,987654321
```
Only sweep these user IDs (comma-separated, no spaces).

---

## What Gets Swept

### ✅ SWEEPS (Moved to Master Wallet)
- Confirmed balance (6+ confirmations)
- User's deposit address completely emptied
- Transaction broadcast to Litecoin mainnet

### ❌ DOESN'T SWEEP (Stays in Deposit Address)
- Unconfirmed balance (pending confirmations)
- Dust amounts below 0.00000546 LTC
- Invalid addresses (skipped)

---

## Step-by-Step Example

### Scenario: You have 3 users who deposited

**Before Sweep:**
```
User A: LYGpJX... → 0.10 LTC (confirmed)
User B: LYGpJY... → 0.05 LTC (confirmed)
User C: LYGpJZ... → 0.02 LTC (confirmed)
Master: Lgtpif... → 0.50 LTC (existing)
```

**After Sweep:**
```
User A: LYGpJX... → 0.00 LTC (empty)
User B: LYGpJY... → 0.00 LTC (empty)
User C: LYGpJZ... → 0.00 LTC (empty)
Master: Lgtpif... → 0.67 LTC (all funds consolidated)
```

---

## Monitoring

### Check Results

After sweep completes, view results:

```powershell
# View summary in console (from logs)
Get-Content tippy_data/sweep.log | Select-Object -Last 50

# View detailed JSON results
Get-Content tippy_data/sweep_results.json | ConvertFrom-Json | Format-List

# Check specific user sweep status
$results = Get-Content tippy_data/sweep_results.json | ConvertFrom-Json
$results.sweeps | Where-Object {$_.user_id -eq '123456789'} | Format-List
```

### Verify on Blockchain

Check master wallet on BlockCypher:
```
https://blockchair.com/litecoin/address/LgtpifMGDFirYSp39esx3zb4v47KgqubBk
```

---

## Error Handling

### Common Issues

**❌ "Invalid address"**
- Address validation failed
- Check `.env` for correct `MASTER_WALLET_ADDRESS`

**❌ "No TX hash returned"**
- Transaction creation failed
- Might be insufficient balance for fees
- Check network status

**❌ "API error"**
- BlockCypher API down
- Check rate limit (200 req/hour)
- Wait and retry

### Recovery

If a sweep fails:

1. **Dry-run again** to see what failed
2. **Check logs** in `tippy_data/sweep.log`
3. **Verify addresses** are valid
4. **Check balance** on blockchain
5. **Retry specific user**: `python bulk_sweep.py --execute --users 123456789`

---

## Safety Checklist

Before running bulk sweep:

- [ ] Run dry-run first (`python bulk_sweep.py`)
- [ ] Review what will be swept
- [ ] Master wallet address is correct
- [ ] Private key is correct (in `.env`)
- [ ] BlockCypher API is accessible
- [ ] Sufficient balance for network fees
- [ ] No time-sensitive transactions pending
- [ ] Have backup of `users.json`
- [ ] Ready to execute (`--execute` flag)

---

## Database Backup

Before bulk sweep, backup user data:

```powershell
# Copy users.json backup
Copy-Item tippy_data/users.json tippy_data/users.json.backup

# Later, if needed, restore
Copy-Item tippy_data/users.json.backup tippy_data/users.json
```

---

## Automating Periodic Sweeps

You can schedule bulk sweep to run periodically:

**Windows Task Scheduler:**
```powershell
# Create scheduled task to sweep daily at 2 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$action = New-ScheduledTaskAction -Execute "python" -Argument "bulk_sweep.py --execute"
Register-ScheduledTask -TaskName "TippyBulkSweep" -Trigger $trigger -Action $action
```

---

## Results File Format

`sweep_results.json`:
```json
{
  "total_users": 3,
  "users_with_balance": 3,
  "successful_sweeps": 3,
  "failed_sweeps": 0,
  "total_swept": 0.17,
  "sweeps": [
    {
      "user_id": "123456789",
      "address": "LYGpJXkCvVrAhR1T7qnVrrCPLLApBTVGKy",
      "amount": 0.10,
      "status": "success",
      "tx_hash": "a1b2c3d4..."
    }
  ]
}
```

---

## Troubleshooting

### Script won't run
```powershell
# Check Python is installed
python --version

# Check dependencies
pip list | grep -E "discord|bitcoinlib|requests"
```

### ModuleNotFoundError
```powershell
# Install missing dependencies
pip install -r requirements.txt
```

### API timeouts
```powershell
# Check internet connection
ping api.blockcypher.com

# Wait a minute and retry
```

---

## Summary

| Task | Command |
|------|---------|
| Preview sweep | `python bulk_sweep.py` |
| Execute sweep | `python bulk_sweep.py --execute` |
| Sweep 1 user | `python bulk_sweep.py --execute --users 123456789` |
| View logs | `Get-Content tippy_data/sweep.log` |
| View results | `Get-Content tippy_data/sweep_results.json` |
| Backup database | `Copy-Item tippy_data/users.json tippy_data/users.json.backup` |

---

## ⚠️ Important Notes

1. **Confirmed Balance Only**: Only sweeps balances with 6+ confirmations
2. **No Pending Funds**: Unconfirmed deposits are not swept
3. **Real Transactions**: With `--execute`, broadcasts actual Litecoin transactions
4. **One-Way**: Swept funds go to master wallet (not reversible)
5. **User Balances**: User database is updated to reflect sweep

---

When you have users with deposits, just run `bulk_sweep.py` to consolidate everything to your master wallet! 🚀
