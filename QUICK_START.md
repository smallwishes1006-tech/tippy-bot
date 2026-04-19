# ⚡ QUICK START - Get Tippy Bot Online in 5 Minutes

## What You Need

1. **GitHub Account** - https://github.com (free)
2. **Railway Account** - https://railway.app (free with $5/month credits)
3. **Your Discord Bot Token** - Already in .env file ✅
4. **Litecoin Wallet Address** - For master wallet (MASTER_WALLET_ADDRESS in .env) ✅

## 5-Minute Setup

### Step 1: Create GitHub Repo
```
Go to https://github.com/new
Name: tippy-bot
Make it PUBLIC
Click "Create repository"
```

### Step 2: Push Your Code

Open PowerShell in project folder:
```powershell
cd C:\Users\small\tippy-bot-clean

git remote add origin https://github.com/YOUR_USERNAME/tippy-bot.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Railway

1. Go to https://railway.app
2. Click "Start Project"
3. Sign in with GitHub
4. Click "New Project" → "GitHub Repo" → Select `tippy-bot`
5. Wait 2-3 minutes for deploy

### Step 4: Add Environment Variables

In Railway dashboard:
1. Click your project
2. Click "Variables"
3. Paste these from your .env file:
   - DISCORD_TOKEN
   - BOT_OWNER_ID
   - MASTER_WALLET_ADDRESS
   - MASTER_WALLET_PRIVATE_KEY
   - BLOCKCYPHER_API_KEY

### Step 5: Verify It's Running

Check Railway logs - you should see:
```
[OK] Bot ready as TippyBot
```

**DONE!** Your bot is now live 24/7 🎉

---

## Your Live Bot URL

Your bot doesn't have an HTTP URL (it's Discord), but it has a **unique public invite**:

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&scope=bot&permissions=8
```

Get YOUR_BOT_ID from:
1. Discord Developer Portal
2. Your Application
3. Copy "Application ID"

---

## Testing Your Bot

Add to Discord server and test:
```
$help
$deposit
$balance
```

## Monitor 24/7

Your bot will:
✅ Run forever (unless you delete the project)
✅ Auto-restart if it crashes
✅ Auto-deploy when you push to GitHub

## Free Tier Details

- **Railway**: $5/month free credits
- **Bot Cost**: ~$1.50/month
- **Your Cost**: FREE (covered by credits)

---

## Support Resources

| Problem | Solution |
|---------|----------|
| Bot not online | Check Railway logs |
| Commands not working | Verify Discord intents enabled |
| No deposits detected | Check BlockCypher API status |
| Want to update code | Push to GitHub, Railway redeploys automatically |

---

## Next Steps

1. ✅ Create GitHub account (if needed)
2. ✅ Follow "5-Minute Setup" above
3. ✅ Test bot with `$help`
4. ✅ Share invite link with friends
5. 📈 Monitor bot growth & stats

**Your Tippy Bot is production-ready!** 🚀

Need help? Check DEPLOYMENT.md for detailed guide.
