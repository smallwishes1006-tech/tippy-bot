## ⚡ RENDER DEPLOYMENT - READY TO GO
**Status:** Code is committed and pushed to GitHub ✅
**Next:** Follow these 4 steps to deploy for 24/7 operation

---

## 🚀 QUICK DEPLOYMENT (5 minutes)

### Step 1: Create Render Account
1. Go to https://render.com
2. Click **"Sign up"** → Choose **"Sign up with GitHub"**
3. Authorize Render to access GitHub
4. Complete setup

### Step 2: Create Worker Service
1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Worker"**
3. Fill in:
   - **Repository:** `smallwishes1006-tech/tippy-bot`
   - **Name:** `tippy-bot`
   - **Runtime:** Docker
   - **Plan:** Free
   - **Region:** Oregon (or closest to you)
4. Click **"Create Web Service"** (will auto-build from Dockerfile)

### Step 3: Add Environment Variables ⚙️
After service is created:
1. Click on your service
2. Go to **"Environment"** tab
3. Click **"Add Environment Variable"** and fill in:

```
DISCORD_TOKEN
Value: [YOUR_DISCORD_BOT_TOKEN]

MASTER_WALLET_ADDRESS
Value: LgtpifMGDFirYSp39esx3zb4v47KgqubBk

MASTER_WALLET_PRIVATE_KEY
Value: [YOUR_MASTER_WALLET_PRIVATE_KEY]

BLOCKCYPHER_API_KEY
Value: [YOUR_BLOCKCYPHER_API_KEY]

BOT_OWNER_ID
Value: 772300666458603520
```

4. **Click "Save"** after each - service will restart

### Step 4: Verify It's Running ✅
1. Go to **"Logs"** tab
2. Watch for these messages:
   ```
   [OK] Bot ready as TippyBot#...
   [OK] Tippy commands loaded
   [CHECKING] Looking for deposits to sweep...
   ```
3. Bot is now running 24/7! ✨

---

## 📊 RENDER FREE TIER (24/7 Operation)

✅ **Fully Free** - $0/month
✅ **24/7 Uptime** - Worker processes run continuously  
✅ **Auto-Deploy** - Updates when you push to GitHub
✅ **Auto-Restart** - Recovers from crashes automatically

---

## 🔍 MONITORING

**View Logs:** Render Dashboard → Logs tab (real-time)
**Check Health:** Service automatically restarts if crashes
**Monitor Bot:** Discord → `/balance` command from bot should work

---

## 🔐 SECURITY NOTES

- Environment variables are encrypted at rest on Render
- Private keys never stored locally, only in Render secrets
- Logs can be viewed only by account owner
- Auto-backup of users.json happens locally in container

---

## 🆘 TROUBLESHOOTING

**Bot offline after deploy?**
→ Check "Logs" tab for errors
→ Verify all env variables are set
→ May take 2-3 minutes to fully start

**Deposits not sweeping?**
→ Check BlockCypher API key is valid
→ Verify MASTER_WALLET_ADDRESS
→ Check logs for "[SWEEP]" messages

**Service keeps restarting?**
→ Check DISCORD_TOKEN is valid
→ Verify all required config variables set
→ Check Logs for error messages

---

## ✨ YOU'RE ALL SET!

All code is ready. The bot is configured for production. Just follow the 4 steps above and you'll have a fully operational 24/7 bot! 

**Questions?** Check RENDER_DEPLOYMENT.md or review the logs on Render dashboard.
