"""
Discord command handlers for Tippy Bot
Prefix commands using $ with rich embed interfaces
"""

import discord
from discord.ext import commands
import logging
import config
from tippy_system import UserAccount, get_user_account, broadcast_withdrawal
from exchange_rates import get_ltc_usd_rate, ltc_to_usd, usd_to_ltc, format_amount
from address_validator import LitecoinValidator

logger = logging.getLogger('tippy_commands')


async def setup(bot):
    """Setup commands for the bot"""
    
    @bot.command(name='deposit', help='Get your deposit address')
    async def deposit(ctx):
        """Get your unique Litecoin deposit address"""
        try:
            user = get_user_account(ctx.author.id)
            rate = get_ltc_usd_rate()
            balance_usd = user.balance * rate
            
            embed = discord.Embed(
                title="[MONEY] Your Deposit Address",
                description="Send Litecoin to this address to fund your account",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Deposit Address (PC Copy)", 
                value=f"```{user.deposit_address}```", 
                inline=False
            )
            embed.add_field(
                name="Deposit Address (Mobile Tap Copy)", 
                value=f"``{user.deposit_address}``", 
                inline=False
            )
            embed.add_field(name="Current Balance", value=format_amount(user.balance, balance_usd), inline=False)
            embed.add_field(name="Network", value="Litecoin Mainnet", inline=True)
            embed.add_field(name="Confirmations", value="6 blocks (~10 min)", inline=True)
            embed.add_field(name="[RATE] Current Rate", value=f"1 LTC = **${rate:.2f}**", inline=False)
            embed.set_footer(text="[SECURE] Never share your private key")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Deposit error: {e}")
            error_embed = discord.Embed(
                title="[FAIL] Error",
                description=str(e)[:100],
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)
    
    
    @bot.command(name='balance', help='Check your balance')
    async def balance(ctx):
        """Check your current balance"""
        try:
            user = get_user_account(ctx.author.id)
            rate = get_ltc_usd_rate()
            balance_usd = user.balance * rate
            received_usd = user.total_received * rate
            sent_usd = user.total_sent * rate
            
            # Calculate confirmed vs unconfirmed
            import requests
            try:
                resp = requests.get(
                    f"https://api.blockcypher.com/v1/ltc/main/addrs/{user.deposit_address}/full",
                    params={"token": config.BLOCKCYPHER_API_KEY or ""},
                    timeout=5
                )
                if resp.status_code == 200:
                    addr_data = resp.json()
                    confirmed = (addr_data.get('final_balance', 0) / 1e8)
                    unconfirmed = ((addr_data.get('balance', 0) - addr_data.get('final_balance', 0)) / 1e8)
                else:
                    confirmed = user.balance
                    unconfirmed = 0
            except:
                confirmed = user.balance
                unconfirmed = 0
            
            embed = discord.Embed(
                title="💵 Your Balance",
                description=f"{format_amount(user.balance)}",
                color=discord.Color.gold()
            )
            embed.add_field(name="Wallet", value=f"`{user.deposit_address[:20]}...`", inline=False)
            embed.add_field(name="[OK] Confirmed", value=format_amount(confirmed, confirmed * rate), inline=True)
            if unconfirmed > 0:
                embed.add_field(name="[WAIT] Pending", value=format_amount(unconfirmed, unconfirmed * rate), inline=True)
            embed.add_field(name="Total Received", value=f"{format_amount(user.total_received, received_usd)}", inline=True)
            embed.add_field(name="Total Sent", value=f"{format_amount(user.total_sent, sent_usd)}", inline=True)
            embed.add_field(name="💱 Current Rate", value=f"1 LTC = **${rate:.2f}**", inline=False)
            embed.set_footer(text="Updated in real-time")
            
            await ctx.send(embed=embed)
            logger.info(f"Balance: {ctx.author.name} ({user.balance:.8f} LTC = ${balance_usd:.2f})")
            
        except Exception as e:
            logger.error(f"Balance error: {e}")
            error_embed = discord.Embed(
                title="[FAIL] Error",
                description=str(e)[:100],
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)
    
    
    @bot.command(name='tip', help='Tip a user in USD')
    async def tip(ctx, member: discord.Member, amount: str):
        """Usage: $tip @user 0.1$ or $tip @user all"""
        try:
            # Check if amount is "all" or in USD format
            if amount.lower() == 'all':
                rate = get_ltc_usd_rate()
                sender = get_user_account(ctx.author.id)
                amount_ltc = sender.balance
                if amount_ltc <= 0:
                    error_embed = discord.Embed(
                        title="[FAIL] No Balance",
                        description="You have no LTC to tip",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
                    return
            elif amount.endswith('$'):
                # Parse amount (remove trailing $)
                amount_str = amount[:-1]
                try:
                    amount_usd = float(amount_str)
                except:
                    error_embed = discord.Embed(
                        title="[FAIL] Invalid Format",
                        description="Usage: `$tip @user 0.1$` or `$tip @user all`",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
                    return
                
                if amount_usd <= 0:
                    error_embed = discord.Embed(
                        title="[FAIL] Invalid Amount",
                        description="Amount must be greater than $0",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
                    return
                
                # Get exchange rate and convert USD to LTC
                rate = get_ltc_usd_rate()
                amount_ltc = usd_to_ltc(amount_usd)
            else:
                error_embed = discord.Embed(
                    title="[FAIL] Invalid Format",
                    description="Usage: `$tip @user 0.1$` (amount in USD) or `$tip @user all`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
                return
            
            # Get sender account
            sender = get_user_account(ctx.author.id)
            rate = get_ltc_usd_rate()
            
            # Check balance
            if sender.balance < amount_ltc:
                balance_usd = sender.balance * rate
                error_embed = discord.Embed(
                    title="[FAIL] Insufficient Balance",
                    description=f"Need: {format_amount(amount_ltc, amount_ltc * rate)}\\nYou have: {format_amount(sender.balance, balance_usd)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
                return
            
            # Get recipient account
            recipient = get_user_account(member.id)
            
            # Transfer
            sender.balance -= amount_ltc
            recipient.balance += amount_ltc
            sender.total_sent += amount_ltc
            recipient.total_received += amount_ltc
            sender.save()
            recipient.save()
            
            amount_usd = amount_ltc * rate
            logger.info(f"TIP: {ctx.author.name} -> {member.name}: ${amount_usd:.2f} ({amount_ltc:.8f} LTC)")
            
            # Send DM to recipient
            try:
                recipient_balance_usd = recipient.balance * rate
                recipient_embed = discord.Embed(
                    title="🎁 Tip Received!",
                    description=f"{ctx.author.name} tipped you {format_amount(amount_ltc, amount_usd)}",
                    color=discord.Color.green()
                )
                recipient_embed.add_field(name="New Balance", value=format_amount(recipient.balance, recipient_balance_usd), inline=False)
                await member.send(embed=recipient_embed)
            except:
                pass
            
            # Confirm to sender (single message)
            sender_balance_usd = sender.balance * rate
            sender_embed = discord.Embed(
                title="[OK] Tip Sent",
                description=f"Sent {format_amount(amount_ltc, amount_usd)} to {member.mention}",
                color=discord.Color.green()
            )
            sender_embed.add_field(name="Your Balance", value=format_amount(sender.balance, sender_balance_usd), inline=False)
            await ctx.send(embed=sender_embed)
            
        except Exception as e:
            logger.error(f"Tip error: {e}")
            error_embed = discord.Embed(
                title="[FAIL] Error",
                description=str(e)[:100],
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)
    
    
    @bot.command(name='withdraw', help='Withdraw LTC to an address')
    async def withdraw(ctx, address: str, amount: str):
        """Usage: $withdraw LTC_ADDRESS 0.1 (LTC) or $withdraw LTC_ADDRESS $50 (USD) or $withdraw LTC_ADDRESS all"""
        try:
            if not isinstance(ctx.channel, discord.DMChannel):
                error_embed = discord.Embed(
                    title="🔐 Security",
                    description="Withdrawals only in **DM** to protect your funds",
                    color=discord.Color.orange()
                )
                error_embed.add_field(name="How to Withdraw", value="Send this command in a DM with Tippy", inline=False)
                await ctx.send(embed=error_embed)
                return
            
            # VALIDATE ADDRESS FIRST
            if not LitecoinValidator.validate_address(address):
                error_embed = discord.Embed(
                    title="❌ Invalid Address",
                    description=f"The address you provided is not a valid Litecoin address",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="Valid Formats",
                    value="• **Legacy**: L... or M... (mainnet)\n• **Segwit**: ltc1... (mainnet)\n• **Testnet**: m/n/2/tltc1...",
                    inline=False
                )
                error_embed.add_field(
                    name="Your Address",
                    value=f"`{address}`",
                    inline=False
                )
                await ctx.send(embed=error_embed)
                logger.warning(f"Invalid withdrawal address from {ctx.author.name}: {address}")
                return
            
            address_type = LitecoinValidator.get_address_type(address)
            logger.info(f"Withdraw to {address_type}: {address}")
            
            # Get exchange rate first
            rate = get_ltc_usd_rate()
            
            # Fee: 0.01$ USD converted to LTC
            SERVICE_FEE_USD = 0.01
            SERVICE_FEE_LTC = usd_to_ltc(SERVICE_FEE_USD)
            
            # Get real-time network fee from BlockCypher
            try:
                import requests
                fee_data = requests.get('https://api.blockcypher.com/v1/ltc/main', timeout=5).json()
                # BlockCypher gives low/medium/high fees in satoshis per KB
                # Use medium fee
                fee_per_kb = fee_data.get('medium_fee_per_kb', 2000)  # fallback to 2000 satoshis/KB
                # Estimate transaction size: ~250 bytes = 0.25 KB, so multiply by 0.25
                CHAIN_FEE_SATOSHIS = max(1000, int(fee_per_kb * 0.25))  # at least 1000 satoshis
                CHAIN_FEE_LTC = CHAIN_FEE_SATOSHIS / 1e8
            except:
                # Fallback if API fails
                CHAIN_FEE_LTC = 0.00002  # 2000 satoshis
            
            user = get_user_account(ctx.author.id)
            
            # ===== RATE LIMITING: Prevent withdrawal spam =====
            import time
            WITHDRAWAL_COOLDOWN_MINUTES = 5
            if user.last_withdrawal_time > 0:
                time_since_last = time.time() - user.last_withdrawal_time
                if time_since_last < (WITHDRAWAL_COOLDOWN_MINUTES * 60):
                    minutes_left = int((WITHDRAWAL_COOLDOWN_MINUTES * 60 - time_since_last) / 60) + 1
                    error_embed = discord.Embed(
                        title="[WAIT] Rate Limited",
                        description=f"Please wait **{minutes_left}m** before next withdrawal",
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=error_embed)
                    return
            
            # Parse amount - support "all" keyword and $ suffix for USD
            if amount.lower() == 'all':
                amount_ltc = user.balance - SERVICE_FEE_LTC - CHAIN_FEE_LTC
                if amount_ltc <= 0:
                    error_embed = discord.Embed(
                        title="[FAIL] Insufficient Balance",
                        description=f"You have: {format_amount(user.balance, user.balance * rate)}\\nNeed at least: {format_amount(SERVICE_FEE_LTC + CHAIN_FEE_LTC, (SERVICE_FEE_LTC + CHAIN_FEE_LTC) * rate)} for fees",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
                    return
            elif amount.endswith('$') or amount.startswith('$'):
                # USD amount format: $50 or 50$
                amount_str = amount.replace('$', '')
                try:
                    amount_usd = float(amount_str)
                    amount_ltc = usd_to_ltc(amount_usd)
                except:
                    error_embed = discord.Embed(
                        title="[FAIL] Invalid Amount",
                        description=f"Use: `$withdraw address 0.1` (LTC) or `$withdraw address $50` (USD) or `$withdraw address all`",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
                    return
            else:
                # LTC amount format (default)
                try:
                    amount_ltc = float(amount)
                except:
                    error_embed = discord.Embed(
                        title="[FAIL] Invalid Amount",
                        description=f"Use: `$withdraw address 0.1` (LTC) or `$withdraw address $50` (USD) or `$withdraw address all`",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
                    return
            
            if amount_ltc <= 0:
                error_embed = discord.Embed(
                    title="[FAIL] Invalid Amount",
                    description="Amount must be greater than 0",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
                return
            
            # User wants to withdraw amount_ltc
            # So they will receive in external wallet: amount_ltc - CHAIN_FEE
            EXTERNAL_RECEIVE_LTC = amount_ltc - CHAIN_FEE_LTC
            
            # Total debit from user = amount_ltc + network fee + service fee
            TOTAL_DEBIT_LTC = amount_ltc + CHAIN_FEE_LTC + SERVICE_FEE_LTC
            
            # Convert to USD
            SERVICE_FEE_USD_DISPLAY = SERVICE_FEE_LTC * rate
            CHAIN_FEE_USD = CHAIN_FEE_LTC * rate
            EXTERNAL_RECEIVE_USD = EXTERNAL_RECEIVE_LTC * rate
            TOTAL_DEBIT_USD = TOTAL_DEBIT_LTC * rate
            
            # Check balance
            if user.balance < TOTAL_DEBIT_LTC:
                have_usd = user.balance * rate
                error_embed = discord.Embed(
                    title="[FAIL] Insufficient Balance",
                    description=f"Need: {format_amount(TOTAL_DEBIT_LTC, TOTAL_DEBIT_USD)}\\nYou have: {format_amount(user.balance, have_usd)}",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="Fee Breakdown", 
                    value=f"Service Fee (0.01$): {format_amount(SERVICE_FEE_LTC, SERVICE_FEE_USD)}\\nChain Fee: {format_amount(CHAIN_FEE_LTC, CHAIN_FEE_USD)}", 
                    inline=False
                )
                await ctx.send(embed=error_embed)
                return
            
            logger.info(f"Withdrawal: {ctx.author.name} -> {address} : {amount_ltc} LTC (External: {EXTERNAL_RECEIVE_LTC}, Fees: {SERVICE_FEE_LTC + CHAIN_FEE_LTC})")
            
            # Send to external wallet from MASTER WALLET (where all funds are swept to)
            tx_hash = broadcast_withdrawal(config.MASTER_WALLET_ADDRESS, address, EXTERNAL_RECEIVE_LTC)
            
            if tx_hash:
                # Debit user: amount they withdraw + service fee
                user.balance -= TOTAL_DEBIT_LTC
                user.total_sent += amount_ltc
                
                # Track withdrawal history
                if user.pending_txs is None:
                    user.pending_txs = []
                if user.withdrawal_history is None:
                    user.withdrawal_history = []
                
                user.pending_txs.append(tx_hash)
                user.withdrawal_history.append({
                    "tx_hash": tx_hash,
                    "amount": amount_ltc,
                    "address": address,
                    "time": time.time(),
                    "status": "pending"
                })
                
                user.save()
                
                # Credit bot owner with service fee
                bot_owner = get_user_account(config.BOT_OWNER_ID, "Tippy_Owner")
                bot_owner.balance += SERVICE_FEE_LTC
                bot_owner.save()
                logger.info(f"[MONEY] Service fee ({SERVICE_FEE_LTC:.8f} LTC) credited to bot owner")
                
                embed = discord.Embed(
                    title="[OK] Withdrawal Confirmed",
                    description="Transaction broadcast to blockchain",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="[SENT] You Requested", 
                    value=format_amount(amount_ltc, amount_ltc * rate), 
                    inline=False
                )
                embed.add_field(
                    name="[MONEY] Fees Paid",
                    value=f"Service (0.01$): {format_amount(SERVICE_FEE_LTC, SERVICE_FEE_USD_DISPLAY)}\nChain: {format_amount(CHAIN_FEE_LTC, CHAIN_FEE_USD)}",
                    inline=False
                )
                embed.add_field(
                    name="[WALLET] External Wallet Receives",
                    value=format_amount(EXTERNAL_RECEIVE_LTC, EXTERNAL_RECEIVE_USD),
                    inline=False
                )
                embed.add_field(name="[TO] To Address", value=f"`{address[:24]}...`", inline=False)
                embed.add_field(name="[HASH] TX Hash", value=f"`{tx_hash}`", inline=False)
                embed.add_field(name="[BALANCE] Your New Balance", value=format_amount(user.balance, user.balance * rate), inline=False)
                embed.add_field(name="[TIME] Confirmations", value="~2.5 min per block (6 blocks ≈ 15 min)", inline=False)
                embed.add_field(name="[RATE] Rate", value=f"1 LTC = **${rate:.2f}**", inline=False)
                embed.set_footer(text="View at: ltc.space or mempool.space")
                await ctx.send(embed=embed)
                
                logger.info(f"SUCCESS: {ctx.author.name} withdrew {amount_ltc} LTC → External: {EXTERNAL_RECEIVE_LTC} LTC - TX: {tx_hash}")
            else:
                error_embed = discord.Embed(
                    title="[FAIL] Broadcast Failed",
                    description="Could not broadcast. Try again or contact support.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
                logger.error(f"Broadcast failed for {ctx.author.name}")
            
        except Exception as e:
            logger.error(f"Withdraw error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            error_embed = discord.Embed(
                title="[FAIL] Error",
                description=str(e)[:100],
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)
    
    
    @bot.command(name='help', help='Show all commands')
    async def show_help(ctx):
        """Show all available commands"""
        rate = get_ltc_usd_rate()
        service_fee_ltc = usd_to_ltc(0.01)
        chain_fee_usd = 0.0005 * rate
        
        embed = discord.Embed(
            title="[HELP] Tippy Bot Commands",
            description="Litecoin Tipping Bot for Discord",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="$deposit",
            value="Get your Litecoin deposit address",
            inline=False
        )
        embed.add_field(
            name="$balance",
            value="Check your balance & wallet stats",
            inline=False
        )
        embed.add_field(
            name="$tip @user amount$ or $tip @user all",
            value="Tip in USD (e.g., `$tip @user 0.5$`) - no fees",
            inline=False
        )
        embed.add_field(
            name="$qtip @user amount$ or $qtip @user all",
            value="Quick tip - instant public response (no fees)",
            inline=False
        )
        embed.add_field(
            name="$withdraw address amount or $withdraw address $amount",
            value="Send to blockchain - Use LTC amount or $USD amount (DM only)",
            inline=False
        )
        embed.add_field(
            name="[MONEY] Fee Structure",
            value=f"**Deposits:** Free\\n**Tips:** Free\\n**Withdrawals:** 0.01$ (${0.01:.2f}) + chain fee (~${chain_fee_usd:.4f})",
            inline=False
        )
        embed.add_field(
            name="$help or $commands",
            value="Show this message",
            inline=False
        )
        
        embed.add_field(name="[SETTINGS] Prefix", value="$", inline=True)
        embed.add_field(name="[RATE] Exchange Rate", value=f"1 LTC = **${rate:.2f}** USD", inline=True)
        embed.set_footer(text="[SECURE] Secure • Efficient • DM-only withdrawals")
        
        await ctx.send(embed=embed)
    
    
    @bot.command(name='cmds', help='Show all commands')
    async def show_commands(ctx):
        """Show all available commands (alias for help)"""
        await show_help(ctx)
    
    
    @bot.command(name='qtip', help='Quick public tip (no fee)')
    async def qtip(ctx, member: discord.Member, amount: str):
        """Usage: $qtip @user 0.1$ or $qtip @user all - Fast public tip"""
        try:
            rate = get_ltc_usd_rate()
            
            # Check if amount is "all" or in USD format
            if amount.lower() == 'all':
                sender = get_user_account(ctx.author.id)
                amount_ltc = sender.balance
                if amount_ltc <= 0:
                    await ctx.send(f"{ctx.author.name}: No balance to tip")
                    return
            elif amount.endswith('$'):
                # Parse amount (remove trailing $)
                amount_str = amount[:-1]
                try:
                    amount_usd = float(amount_str)
                except:
                    await ctx.send(f"{ctx.author.name}: Invalid amount '{amount_str}'")
                    return
                
                if amount_usd <= 0:
                    await ctx.send(f"{ctx.author.name}: Amount must be > $0")
                    return
                
                amount_ltc = usd_to_ltc(amount_usd)
            else:
                await ctx.send(f"{ctx.author.name}: Use `$qtip @user 0.1$` or `$qtip @user all`")
                return
            
            sender = get_user_account(ctx.author.id)
            
            if sender.balance < amount_ltc:
                await ctx.send(f"{ctx.author.name}: Need {format_amount(amount_ltc, amount_ltc * rate)}, have {format_amount(sender.balance, sender.balance * rate)}")
                return
            
            recipient = get_user_account(member.id)
            
            sender.balance -= amount_ltc
            recipient.balance += amount_ltc
            sender.total_sent += amount_ltc
            recipient.total_received += amount_ltc
            sender.save()
            recipient.save()
            
            # Quick public response with USD
            amount_usd = amount_ltc * rate
            sender_usd = sender.balance * rate
            recipient_usd = recipient.balance * rate
            await ctx.send(f"[OK] {ctx.author.name} → {member.name}: {format_amount(amount_ltc, amount_usd)} | {ctx.author.name}: {format_amount(sender.balance, sender_usd)} | {member.name}: {format_amount(recipient.balance, recipient_usd)}")
            
            logger.info(f"QTIP: {ctx.author.name} -> {member.name}: {amount_ltc} LTC")
            
        except Exception as e:
            logger.error(f"Qtip error: {e}")
            await ctx.send(f"{ctx.author.name}: Error - {str(e)[:50]}")
    
    
    @bot.command(name='commands', help='Show all commands')
    async def commands_alias(ctx):
        """Alias for help"""
        await show_help(ctx)
    
    
    @bot.command(name='history', help='View your withdrawal history')
    async def withdrawal_history(ctx):
        """Show last 5 withdrawals"""
        try:
            user = get_user_account(ctx.author.id)
            rate = get_ltc_usd_rate()
            
            if not user.withdrawal_history or len(user.withdrawal_history) == 0:
                embed = discord.Embed(
                    title="📋 Withdrawal History",
                    description="No withdrawals yet",
                    color=discord.Color.blurple()
                )
                await ctx.send(embed=embed)
                return
            
            # Show last 5 withdrawals
            recent = user.withdrawal_history[-5:]
            
            embed = discord.Embed(
                title=f"📋 Last {len(recent)} Withdrawal(s)",
                color=discord.Color.blurple()
            )
            
            for tx in reversed(recent):
                status_emoji = "[OK]" if tx.get('status') == 'confirmed' else "[WAIT]"
                amount_ltc = tx.get('amount', 0)
                amount_usd = amount_ltc * rate
                embed.add_field(
                    name=f"{status_emoji} {format_amount(amount_ltc, amount_usd)}",
                    value=f"To: `{tx['address'][:24]}...`\\nTime: <t:{int(tx.get('time', 0))}:R>",
                    inline=False
                )
            
            embed.set_footer(text="View full TX at ltc.space or mempool.space")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"History error: {e}")
            await ctx.send(f"[FAIL] Error: {str(e)[:100]}")
    
    
    @bot.command(name='status', help='Check pending transaction status')
    async def check_status(ctx, tx_hash: str = None):
        """Check withdrawal transaction status"""
        try:
            import requests
            
            # If no TX provided, show user's pending txs
            if not tx_hash:
                user = get_user_account(ctx.author.id)
                
                if not user.pending_txs or len(user.pending_txs) == 0:
                    embed = discord.Embed(
                        title="[OK] All Clear",
                        description="No pending transactions",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = discord.Embed(
                    title=f"[WAIT] Pending Transactions ({len(user.pending_txs)})",
                    color=discord.Color.orange()
                )
                
                for tx in user.pending_txs[-3:]:  # Show last 3
                    embed.add_field(
                        name="📍 Hash",
                        value=f"`{tx[:20]}...`",
                        inline=False
                    )
                
                embed.set_footer(text="Use $status <tx_hash> to check specific TX")
                await ctx.send(embed=embed)
                return
            
            # Check specific TX
            url = f"https://api.blockcypher.com/v1/ltc/main/txs/{tx_hash}"
            resp = requests.get(url, timeout=5)
            
            if resp.status_code != 200:
                await ctx.send(f"[FAIL] Transaction not found: {tx_hash[:20]}...")
                return
            
            data = resp.json()
            confirmed = "confirmed" in data and data["confirmed"]
            confirmations = data.get("confirmations", 0)
            
            embed = discord.Embed(
                title=f"{'[OK] Confirmed' if confirmed else '[WAIT] Pending'}",
                description=f"Confirmations: **{confirmations}** (need 6)",
                color=discord.Color.green() if confirmed else discord.Color.orange()
            )
            
            embed.add_field(
                name="📍 TX Hash",
                value=f"```{tx_hash}```",
                inline=False
            )
            
            if data.get('inputs') and len(data['inputs']) > 0:
                embed.add_field(
                    name="📤 From",
                    value=f"`{data['inputs'][0]['addresses'][0][:24]}...`",
                    inline=False
                )
            
            if data.get('outputs') and len(data['outputs']) > 0:
                for i, out in enumerate(data['outputs']):
                    if i == 0:  # Only show main output
                        embed.add_field(
                            name="📥 To",
                            value=f"`{out['addresses'][0][:24] if out.get('addresses') else 'Unknown'}...`",
                            inline=False
                        )
            
            embed.set_footer(text="View full TX at ltc.space or mempool.space")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            await ctx.send(f"[FAIL] Error checking TX: {str(e)[:100]}")
    
    
    
    # ===== COMMAND ALIASES (short versions) =====
    
    @bot.command(name='bal', help='Check balance (short)')
    async def balance_short(ctx):
        """Alias for balance"""
        await balance(ctx)
    
    @bot.command(name='dep', help='Get deposit address (short)')
    async def deposit_short(ctx):
        """Alias for deposit"""
        await deposit(ctx)
    
    @bot.command(name='t', help='Tip a user (short)')
    async def tip_short(ctx, member: discord.Member, amount: str):
        """Alias for tip"""
        await tip(ctx, member, amount)
    
    @bot.command(name='qt', help='Quick tip (short)')
    async def qtip_short(ctx, member: discord.Member, amount: str):
        """Alias for qtip"""
        await qtip(ctx, member, amount)
    
    @bot.command(name='wd', help='Withdraw to address (short)')
    async def withdraw_short(ctx, address: str, amount: str):
        """Alias for withdraw"""
        await withdraw(ctx, address, amount)
    
    @bot.command(name='hist', help='Withdrawal history (short)')
    async def history_short(ctx):
        """Alias for history"""
        await withdrawal_history(ctx)
    
    @bot.command(name='st', help='Check TX status (short)')
    async def status_short(ctx, tx_hash: str = None):
        """Alias for status"""
        await check_status(ctx, tx_hash)
    
    @bot.command(name='h', help='Show help (short)')
    async def help_short(ctx):
        """Alias for help"""
        await show_help(ctx)
    
    @bot.command(name='cmd', help='Show commands (short)')
    async def cmd_short(ctx):
        """Alias for commands"""
        await show_commands(ctx)
    
    logger.info("[OK] Tippy commands loaded with 11 commands + 9 aliases")

