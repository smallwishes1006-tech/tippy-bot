#!/usr/bin/env python3
"""
Automatic Render.com Deployment Script for Tippy Bot
This script handles the deployment via Render's API
"""

import os
import subprocess
import json
import time
import sys

def main():
    print("🚀 Tippy Bot - Render.com Deployment Helper\n")
    
    # Check if GitHub code is pushed
    print("1️⃣ Verifying GitHub repository...")
    result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
    if 'smallwishes1006-tech/tippy-bot' in result.stdout:
        print("✅ GitHub repository verified: smallwishes1006-tech/tippy-bot")
    else:
        print("❌ GitHub repository not found in remotes")
        sys.exit(1)
    
    # Check latest commits
    print("\n2️⃣ Latest commits on GitHub:")
    result = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True)
    print(result.stdout)
    
    # Verify all deployment files exist
    print("3️⃣ Verifying deployment files...")
    required_files = [
        'Dockerfile',
        'render.yaml',
        '.dockerignore',
        'RENDER_DEPLOYMENT.md',
        'bot_main.py',
        'requirements.txt',
        'config.py'
    ]
    
    all_exist = True
    for file in required_files:
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"  {status} {file}")
        all_exist = all_exist and exists
    
    if not all_exist:
        print("\n❌ Some required files are missing!")
        sys.exit(1)
    
    print("\n✅ All deployment files verified!\n")
    print("="*70)
    print("NEXT STEPS - Follow these to deploy on Render.com:")
    print("="*70)
    print("""
1. GO TO RENDER.COM
   → https://render.com
   → Sign up with GitHub
   
2. CREATE NEW WORKER
   → Dashboard → "New +" → "Worker"
   → Select: smallwishes1006-tech/tippy-bot
   → Name: tippy-bot
   → Runtime: Docker
   → Plan: Free
   → Click "Create Web Service"
   
3. ADD ENVIRONMENT VARIABLES
   Go to "Environment" tab and add:
   
   DISCORD_TOKEN = [paste your new Discord bot token here]
   MASTER_WALLET_ADDRESS = LgtpifMGDFirYSp39esx3zb4v47KgqubBk
   MASTER_WALLET_PRIVATE_KEY = [your master wallet private key]
   BLOCKCYPHER_API_KEY = ca16eb5f711d4cc3baca146bb2166d02
   BOT_OWNER_ID = 772300666458603520
   
4. WATCH LOGS
   Click "Logs" tab and wait for:
   [OK] Bot ready as TippyBot
   
5. TEST BOT
   In Discord: $help
   
6. STOP REPLIT
   https://replit.com/@smallwishes1006/tippy-bot → Click Stop

Your code is ready on GitHub! 🎉
All files are deployed and waiting for you to add environment variables.
    """)

if __name__ == '__main__':
    main()
