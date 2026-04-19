# 🚀 Deploy Tippy Bot to Render.com (FREE & RELIABLE)

## Why Render.com?
✅ **Completely FREE** - No trial, no credits that expire
✅ **24/7 Uptime** - Worker processes run continuously
✅ **Auto-Deploy** - Updates automatically when you push to GitHub
✅ **Reliable** - No cold starts, no downtime
✅ **Easy Setup** - 5 minutes to deploy

---

## 📋 Prerequisites
- GitHub account (already set up ✓)
- Render.com account (FREE)
- New Discord bot token ✓

---

## 🚀 Step-by-Step Deployment

### Step 1: Create Render.com Account
1. Go to https://render.com
2. Click **"Sign up"**
3. Choose **"Sign up with GitHub"**
4. Authorize Render to access your GitHub repos
5. Complete profile setup

### Step 2: Deploy from GitHub
1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Worker"**
3. Select repository: **`smallwishes1006-tech/tippy-bot`**
4. Name: `tippy-bot`
5. Runtime: **Docker**
6. Plan: **Free** (shows $0/month)
7. Region: Choose closest to you (or `oregon`)
8. Click **"Create Web Service"** (it will auto-build)

### Step 3: Add Environment Variables
Once service is created:
1. Go to service **"Environment"** tab
2. Add these variables (copy-paste exact values):

| Key | Value |
|-----|-------|
| `DISCORD_TOKEN` | `YOUR_DISCORD_TOKEN_HERE` |
| `MASTER_WALLET_ADDRESS` | `LgtpifMGDFirYSp39esx3zb4v47KgqubBk` |
| `MASTER_WALLET_PRIVATE_KEY` | `YOUR_PRIVATE_KEY_HERE` |
| `BLOCKCYPHER_API_KEY` | `YOUR_BLOCKCYPHER_API_KEY_HERE` |
| `BOT_OWNER_ID` | `772300666458603520` |

3. Click **"Save"** after each variable
4. Service will automatically restart with new variables

### Step 4: Verify Deployment
1. Go to **"Logs"** tab
2. Watch for:
   ```
   [OK] Bot ready as TippyBot
   📥 Monitoring deposits every 5 minutes
   📤 Monitoring pending withdrawals every 2 minutes
   ```
3. Once you see these messages, bot is online! ✅

### Step 5: Test in Discord
In any Discord channel with the bot:
```
$help
```

Bot should respond with command list. If it works, deployment successful! 🎉

---

## 📊 Free Tier Details

| Feature | Free Tier |
|---------|-----------|
| **Monthly Cost** | $0 |
| **Worker Dynos** | Unlimited |
| **Uptime** | 24/7 |
| **Build Time** | 500 hours/month (plenty for Discord bot) |
| **Auto-Deploy** | ✅ Yes |
| **Cold Starts** | ❌ None (always on) |

---

## 🔄 Auto-Deploy from GitHub

Every time you push to GitHub, Render automatically:
1. Pulls latest code
2. Rebuilds Docker image
3. Restarts the bot with new code
4. Zero downtime

No manual intervention needed!

---

## 🛑 Stop Replit Bot

Once Render bot is confirmed online:

1. Go to https://replit.com/@smallwishes1006/tippy-bot
2. Click **Stop** button
3. Wait for bot to go offline in Discord
4. Replit costs stop immediately

---

## 🔧 Troubleshooting

### Bot doesn't start
**Check logs in Render dashboard** for error messages:
- Missing environment variable
- Invalid Discord token
- Network error

### Bot offline despite being deployed
1. Verify DISCORD_TOKEN is correct in Render env vars
2. Check Discord bot has permissions in server
3. Check Render logs for crashes

### Want to view logs
Render Dashboard → Your Service → **Logs** tab

---

## 📝 Notes

- `.env` file is local-only (safe - not in git)
- Sensitive data is stored in Render environment variables (secure)
- Docker image rebuilds on every GitHub push (auto-deploy)
- Completely free - no expiration date

---

## ✨ You're Done!

Your Tippy Bot is now:
✅ On GitHub
✅ Auto-deploying from GitHub
✅ Running 24/7 on Render.com
✅ Completely FREE

No more Replit costs, no more trial expiration! 🚀
