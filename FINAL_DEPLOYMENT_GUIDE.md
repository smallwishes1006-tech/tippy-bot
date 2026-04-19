# 🚀 Complete Tippy Bot Deployment Guide

## ✅ Completed Setup
- **Code Repository**: All 23 files ready in C:\Users\small\tippy-bot-clean
- **Git Status**: 12 commits prepared, .env removed from tracking
- **Code Location**: Ready to push to https://github.com/smallwishes1006-tech/tippy-bot

## ⚠️ STEP 1: Unblock Discord Token on GitHub (REQUIRED)

GitHub's security detected your Discord token in historical commits and blocked the push.

**Action Required:**
1. Visit: https://github.com/smallwishes1006-tech/tippy-bot/security/secret-scanning/unblock-secret/3CYr1g57JA4vCpX1w5hrSH55rSv
2. Click **"Allow"** to authorize the token push
3. Confirm the action

**OR Rotate the Token (More Secure):**
1. Go to https://discord.com/developers/applications
2. Select your TippyBot application
3. Click **"Reset Token"** under TOKEN section
4. Copy the new token
5. Come back and tell me the new token, I'll update it everywhere

---

## 📤 STEP 2: Push Code to GitHub (After Unblocking)

Once you've unblocked the secret on GitHub, I'll run:
```powershell
cd C:\Users\small\tippy-bot-clean
git push -u origin main --force
```

This will upload all code to your repository.

---

## 🚀 STEP 3: Deploy to Railway.app

### 3.1 Create Railway Account
1. Go to https://railway.app
2. Click **"Start Project"** → **"GitHub"**
3. Authorize Railway to access your GitHub
4. Select your `tippy-bot` repository from the list

### 3.2 Configure Environment Variables
Railway dashboard → Your Project → **"Variables"** tab → Add:

```
DISCORD_TOKEN=<your_bot_token>
MASTER_WALLET_ADDRESS=LgtpifMGDFirYSp39esx3zb4v47KgqubBk
MASTER_WALLET_PRIVATE_KEY=T4TV9opCaTfGhzNuYVNMCcziJAUA3un5pSSQ5UumcLtsAPUeHePo
BLOCKCYPHER_API_KEY=ca16eb5f711d4cc3baca146bb2166d02
```

### 3.3 Deploy
1. Click **"Deploy"** button
2. Watch logs until you see: `[OK] Bot ready as TippyBot`
3. Bot should come online automatically

---

## 📋 Project Contents (Ready to Deploy)

### Core Bot Files
- **bot_main.py** - Main Discord bot with background tasks
- **config.py** - Configuration (wallet, API keys)
- **tippy_commands.py** - 7 Discord commands ($deposit, $balance, $tip, $withdraw, $qtip, $help)
- **tippy_system.py** - User account system with JSON storage

### Security & Blockchain Modules
- **address_validator.py** - Validates Litecoin addresses (P2PKH, P2SH, Bech32)
- **litecoin_signer.py** - Transaction signing via BlockCypher
- **exchange_rates.py** - CoinGecko API for USD/LTC rates

### Utilities
- **bulk_sweep.py** - Consolidate all user addresses to master wallet
- **test_sweep.py** - Validate sweep setup

### Configuration
- **Procfile** - Railway worker config: `worker: python bot_main.py`
- **requirements.txt** - Python dependencies (discord.py 2.3.2, bitcoinlib, etc.)
- **.gitignore** - Protects .env from commits

### Documentation  
- **README.md** - Project overview
- **DEPLOYMENT.md** - Deployment instructions
- **FUNCTIONALITY_ASSESSMENT.md** - Bot feature assessment
- **BULK_SWEEP_GUIDE.md** - How to consolidate user wallets

---

## 💰 Wallet Configuration

**Master Wallet (Custodial):**
- Address: `LgtpifMGDFirYSp39esx3zb4v47KgqubBk`
- Network: Litecoin Mainnet
- Type: P2PKH (Standard address)

**How It Works:**
1. Users deposit LTC to unique deposit addresses (generated per user)
2. Bot monitors blockchain and credits balances automatically
3. Withdrawals transfer from master wallet to user address
4. Withdrawal fees go to owner: Discord ID 772300666458603520

---

## 🔧 Bot Commands

| Command | Usage | Example |
|---------|-------|---------|
| `$help` | Show all commands | `$help` |
| `$deposit` | Get your deposit address | `$deposit` |
| `$balance` | Check your balance | `$balance` |
| `$tip @user amount` | Tip another user | `$tip @alice 0.5` |
| `$qtip amount` | Quick tip using quick tip pool | `$qtip 0.1` |
| `$withdraw address` | Withdraw to address | `$withdraw LgtpifMGDFirYSp39esx3zb4v47KgqubBk` |

---

## 📊 Deployment Checklist

- [ ] Step 1: Unblock Discord token on GitHub
- [ ] Step 2: Wait for code to push to GitHub
- [ ] Step 3: Create Railway account
- [ ] Step 3.2: Add environment variables to Railway
- [ ] Step 3.3: Deploy and watch logs
- [ ] Step 4: Test bot with `$help` command in Discord
- [ ] Step 5: Stop Replit bot (once Railway bot is confirmed online)

---

## ✨ After Deployment

### Verify Bot is Online
In Discord channel with bot access:
```
$help
```

If bot responds with command list, deployment successful! ✅

### Monitor Logs
Railway dashboard → Logs tab → Watch for:
- `[OK] Bot ready as TippyBot` - Bot connected successfully
- `📥 Monitoring deposits every 5 minutes`
- `📤 Monitoring pending withdrawals every 2 minutes`

### Troubleshooting
- **Bot not responding**: Check Discord bot permissions in server settings
- **Bot crashes on startup**: Check environment variables in Railway
- **Build fails**: Check `requirements.txt` dependencies are compatible

---

## 🛑 Stop Replit Bot

Once Railway bot is confirmed online:

1. Go to https://replit.com/@smallwishes1006/tippy-bot
2. Click the **"Stop"** button on the Replit console
3. Verify TippyBot goes offline in Discord
4. Replit costs will stop immediately

---

## 📞 Support

If issues occur after deployment:
1. Check Railway logs for error messages
2. Verify all environment variables are set correctly
3. Ensure Discord bot has necessary permissions:
   - Send Messages
   - Read Message History
   - Manage Roles (for admin commands)
4. Check Litecoin blockchain confirmations for deposits

---

**Status:** All code is committed and ready to push. Awaiting GitHub secret unblock to finalize deployment.
