# 🚀 Tippy Bot - Litecoin Discord Tipping Bot

A production-ready Discord bot for tipping with Litecoin (LTC). Use $ prefix commands to deposit, tip, check balance, and withdraw.

## Features

- 💰 **Deposit**: Get unique Litecoin address for funding
- 💸 **Tip**: Send LTC to other Discord users (no fees)
- 💵 **Withdraw**: Send to any Litecoin address (DM only for security)
- 📊 **Balance**: Check confirmed/unconfirmed balance and stats
- 🔄 **Real-time Exchange Rates**: USD ↔ LTC conversion
- ⚡ **Custodial Model**: Auto-sweep deposits to master wallet
- 🛡️ **Secure**: Private keys never exposed, withdrawal confirmations tracked

## Commands

```
$deposit          - Get your deposit address
$balance          - Check your balance
$tip @user 0.5$   - Tip in USD
$qtip @user 0.5$  - Quick tip (public response)
$withdraw addr 0.1 - Withdraw to blockchain (DM only)
$help             - Show all commands
```

## Tech Stack

- **Python 3.8+**
- **discord.py** - Discord bot framework
- **bitcoinlib** - Litecoin transaction signing
- **BlockCypher API** - Blockchain data & broadcasting
- **CoinGecko API** - Exchange rates (free, no auth)

## Deployment

### Railway.app (Recommended - Free)

1. Push to GitHub
2. Connect to Railway: https://railway.app
3. Set environment variables
4. Deploy (automatic)

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up .env file
cp .env.example .env
# Edit .env with your DISCORD_TOKEN, MASTER_WALLET_ADDRESS, etc.

# Run bot
python bot_main.py
```

## Environment Variables

```env
DISCORD_TOKEN=your_discord_token
BOT_OWNER_ID=your_discord_id
MASTER_WALLET_ADDRESS=ltc_wallet_address
MASTER_WALLET_PRIVATE_KEY=private_key_wif
BLOCKCYPHER_API_KEY=your_api_key (free tier)
```

## Fee Structure

- **Deposits**: Free
- **Tips**: Free (internal transfers)
- **Withdrawals**: $0.01 USD + network fee
- **Min Withdrawal**: $0.02 USD

## Security

- Withdrawal commands only work in DM
- Private keys stored encrypted in JSON
- No hot wallet - funds swept to master after deposit confirmation
- 6-block confirmation requirement

## Support

For issues or questions, create a GitHub issue or contact the bot owner.

---

**Litecoin Mainnet** | **Production Ready** | **24/7 Uptime** 🎯
