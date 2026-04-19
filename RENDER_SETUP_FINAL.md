# ?? TIPPY BOT - RENDER DEPLOYMENT GUIDE (FINAL)

## STEP 1: Add Environment Variables to Render Dashboard

Go to: **https://render.com ? Select your tippy-bot service ? Environment**

Add these variables ONE BY ONE:

### CRITICAL (Must have):
```
DISCORD_TOKEN=[USE YOUR OWN TOKEN FROM DEVELOPER PORTAL]
MASTER_WALLET_ADDRESS=[USE YOUR OWN LITECOIN ADDRESS]
MASTER_WALLET_PRIVATE_KEY=[USE YOUR OWN PRIVATE KEY]
BOT_OWNER_ID=772300666458603520
```

### RECOMMENDED (Good to have):
```
MONGO_URI=mongodb://admin:secure_password@localhost:27017/tippy_bot?authSource=admin
BLOCKCYPHER_API_KEY=[USE YOUR OWN API KEY]
NETWORK=mainnet
MIN_TIP_AMOUNT=0.001
MAX_TIP_AMOUNT=100.0
LOG_LEVEL=INFO
```

## STEP 2: Verify Git Push

Make sure latest code is pushed to GitHub:
```powershell
cd c:\Users\small\tippy-bot-clean
git status
git add .
git commit -m "Update Discord token for production"
git push origin main
```

## STEP 3: Redeploy on Render

1. Go to your service dashboard
2. Click **"Manual Deploy"** or **"Redeploy Latest Commit"**
3. Wait for build to complete (3-5 minutes)
4. Check logs for: `[OK] Bot ready as [BotName]`

## STEP 4: Test Bot

In Discord, use your bot with `$` prefix:
```
$help          - Show commands
$balance       - Check your balance
$deposit       - Get deposit address
```

## TROUBLESHOOTING

### Still getting 401 error?
- Check that DISCORD_TOKEN matches exactly (no spaces)
- Verify token in Discord Developer Portal is NOT disabled
- Regenerate a new token if needed

### Bot not responding to commands?
- Check Render logs for Python errors
- Verify DISCORD_TOKEN is valid
- Make sure bot has permissions in Discord server

### Deposits not working?
- Check MASTER_WALLET_ADDRESS is valid Litecoin address (starts with L)
- Verify MASTER_WALLET_PRIVATE_KEY matches the address
- Check BlockCypher API working: https://www.blockcypher.com/v1/ltc/main/txs/

## IMPORTANT SECURITY NOTES

?? **Never commit .env file to Git**
- It's already in .gitignore
- Environment variables are secrets - keep them safe

? **Rotate token if exposed**
- If token appears in git history, regenerate in Discord Developer Portal
- Delete the old bot application

? **Monitor logs regularly**
- Check Render logs daily for errors
- Subscribe to error alerts in Render dashboard
