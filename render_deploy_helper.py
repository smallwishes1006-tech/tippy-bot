#!/usr/bin/env python3
"""
RENDER DEPLOYMENT AUTOMATION HELPER
This script provides all necessary info to deploy to Render for 24/7 operation
"""

import os
import sys

# Configuration - Set these in your Render environment variables
# Do NOT hardcode secrets in this file
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_TOKEN_HERE")
MASTER_WALLET_ADDRESS = os.getenv("MASTER_WALLET_ADDRESS", "YOUR_WALLET_HERE")
BLOCKCYPHER_API_KEY = os.getenv("BLOCKCYPHER_API_KEY", "YOUR_API_KEY_HERE")
BOT_OWNER_ID = os.getenv("BOT_OWNER_ID", "YOUR_ID_HERE")
GITHUB_REPO = "smallwishes1006-tech/tippy-bot"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(text.center(70))
    print("="*70)

def print_section(title):
    """Print a section divider"""
    print(f"\n--- {title} ---")

def main():
    """Main function"""
    print_header("RENDER DEPLOYMENT HELPER FOR 24/7 BOT OPERATION")
    
    print_section("ENVIRONMENT VARIABLES TO SET IN RENDER")
    print("""
Set the following environment variables in your Render service settings:
  - DISCORD_TOKEN: Your Discord bot token
  - MASTER_WALLET_ADDRESS: Your wallet address for transactions
  - BLOCKCYPHER_API_KEY: BlockCypher API key for blockchain operations
  - BOT_OWNER_ID: Your Discord user ID
  - GITHUB_TOKEN: (Optional) For automated deployments
""")
    
    print_section("RENDER SERVICE SETUP REQUIREMENTS")
    print("""
1. Create a new Web Service on Render
2. Connect your GitHub repository: smallwishes1006-tech/tippy-bot
3. Set Build Command: pip install -r requirements.txt
4. Set Start Command: python bot.py
5. Select a paid plan (free tier doesn't support 24/7)
6. Add all required environment variables
7. Enable auto-deploy from main branch (optional)
""")
    
    print_section("KEY FILES NEEDED")
    print("""
- requirements.txt: Python dependencies
- bot.py: Main bot entry point
- .env.example: Template for environment variables (for documentation only)
""")
    
    print_section("24/7 OPERATION SETUP")
    print("""
To keep your bot running 24/7 on Render:
1. Use a paid Render plan (Starter or higher)
2. Set Keep Alive: Enable in service settings
3. Recommended: Add a simple HTTP endpoint to prevent hibernation
4. Monitor logs in Render dashboard
5. Set up alerts for service failures
""")
    
    print_section("DEPLOYMENT STEPS")
    print("""
1. Push your code to the main branch
2. Render will automatically trigger a build (if auto-deploy enabled)
3. Monitor the deployment in Render dashboard
4. Verify bot is online in Discord
5. Check logs for any errors
""")

if __name__ == "__main__":
    main()
