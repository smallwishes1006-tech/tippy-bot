"""
Litecoin transaction signing and broadcasting
Uses bitcoinlib library for Litecoin transaction creation
"""

import logging
import requests
from bitcoinlib.keys import Key
from bitcoinlib.wallets import wallet_create_or_open, wallet_delete_if_exists
from bitcoinlib.mnemonic import Mnemonic
import config

logger = logging.getLogger('litecoin_signer')


class LitecoinSigner:
    """Handle Litecoin transaction signing and broadcasting"""
    
    @staticmethod
    def withdraw(
        from_address: str,
        to_address: str,
        amount: float,
        private_key_wif: str,
        use_rbf: bool = True
    ) -> str:
        """
        Create and broadcast a withdrawal transaction
        
        Args:
            from_address: Source Litecoin address
            to_address: Destination Litecoin address
            amount: Amount in LTC to send
            private_key_wif: Private key in WIF format
            use_rbf: Enable Replace-By-Fee
            
        Returns:
            Transaction hash or None
        """
        try:
            logger.info(f"Creating withdrawal: {amount} LTC to {to_address}")
            
            # Get current network fee from BlockCypher
            try:
                fee_resp = requests.get(
                    'https://api.blockcypher.com/v1/ltc/main',
                    timeout=5
                )
                if fee_resp.status_code == 200:
                    fee_data = fee_resp.json()
                    fee_per_kb = fee_data.get('medium_fee_per_kb', 2000)  # satoshis/KB
                else:
                    fee_per_kb = 2000
            except:
                fee_per_kb = 2000  # Fallback
            
            # Get UTXOs from BlockCypher
            try:
                utxo_resp = requests.get(
                    f"https://api.blockcypher.com/v1/ltc/main/addrs/{from_address}/full",
                    params={"token": config.BLOCKCYPHER_API_KEY or ""},
                    timeout=5
                )
                
                if utxo_resp.status_code != 200:
                    logger.error(f"Could not get UTXOs: {utxo_resp.status_code}")
                    return None
                
                addr_data = utxo_resp.json()
                utxos = addr_data.get('txrefs', [])
                
                if not utxos:
                    logger.error(f"No unspent outputs at {from_address}")
                    return None
                
                # Filter for confirmed UTXOs only
                confirmed_utxos = [u for u in utxos if not u.get('spent') and u.get('confirmations', 0) >= config.CONFIRMATION_BLOCKS]
                
                if not confirmed_utxos:
                    logger.warning(f"No confirmed UTXOs at {from_address}, trying unconfirmed...")
                    confirmed_utxos = [u for u in utxos if not u.get('spent')]
                
                if not confirmed_utxos:
                    logger.error(f"No available UTXOs at {from_address}")
                    return None
                
                # Calculate fee
                # Estimate TX size: 148 bytes per input + 34 bytes per output + 10 bytes overhead
                # Assume 1 input, 2 outputs (recipient + change)
                estimated_size = 148 + (34 * 2) + 10
                estimated_fee = int((estimated_size / 1000) * fee_per_kb)
                
                # Ensure minimum fee
                estimated_fee = max(1000, estimated_fee)  # At least 1000 satoshis
                estimated_fee_ltc = estimated_fee / 1e8
                
                logger.info(f"Estimated fee: {estimated_fee_ltc:.8f} LTC ({estimated_fee} satoshis)")
                
                # Use bitcoinlib to create transaction
                wallet_name = f"withdrawal_{from_address[:10]}"
                
                try:
                    wallet_delete_if_exists(wallet_name, force=True)
                except:
                    pass
                
                # Create wallet from private key
                wallet = wallet_create_or_open(
                    wallet_name,
                    keys=private_key_wif,
                    network='litecoin',
                    witness_type='legacy'
                )
                
                # Create transaction
                key = Key(private_key_wif, network='litecoin')
                
                # Calculate total input and output
                total_input = sum(u.get('output_value', 0) for u in confirmed_utxos) / 1e8
                total_output = amount + estimated_fee_ltc
                
                if total_input < total_output:
                    logger.error(f"Insufficient funds: have {total_input:.8f}, need {total_output:.8f}")
                    return None
                
                change_amount = total_input - total_output
                
                # Use BlockCypher's transaction creation API
                tx_data = {
                    "inputs": [
                        {
                            "addresses": [from_address],
                            "output_index": u.get('tx_output_n', 0)
                        }
                        for u in confirmed_utxos[:5]  # Limit to 5 inputs
                    ],
                    "outputs": [
                        {
                            "addresses": [to_address],
                            "value": int(amount * 1e8)  # Convert to satoshis
                        }
                    ]
                }
                
                # Add change if > dust limit
                if change_amount > 0.00000546:  # Dust limit
                    tx_data["outputs"].append({
                        "addresses": [from_address],
                        "value": int(change_amount * 1e8)
                    })
                
                # Create and sign transaction via BlockCypher
                new_tx_resp = requests.post(
                    'https://api.blockcypher.com/v1/ltc/main/txs/new',
                    json=tx_data,
                    params={"token": config.BLOCKCYPHER_API_KEY or ""},
                    timeout=10
                )
                
                if new_tx_resp.status_code != 201:
                    logger.error(f"Transaction creation failed: {new_tx_resp.status_code}")
                    logger.error(new_tx_resp.text)
                    return None
                
                tx_skeleton = new_tx_resp.json()
                
                # Sign each input
                for idx in range(len(tx_skeleton.get('inputs', []))):
                    # Get the hash to sign
                    hash_to_sign = tx_skeleton['tosign'][idx]
                    
                    # Sign with private key
                    from bitcoinlib.keys import HDKey
                    key_obj = HDKey(private_key_wif, network='litecoin')
                    signature = key_obj.sign(bytes.fromhex(hash_to_sign))
                    
                    tx_skeleton['signatures'].append(signature.hex())
                
                # Send signed transaction
                send_resp = requests.post(
                    'https://api.blockcypher.com/v1/ltc/main/txs/send',
                    json=tx_skeleton,
                    params={"token": config.BLOCKCYPHER_API_KEY or ""},
                    timeout=10
                )
                
                if send_resp.status_code not in [200, 201]:
                    logger.error(f"Transaction broadcast failed: {send_resp.status_code}")
                    logger.error(send_resp.text)
                    return None
                
                tx_hash = send_resp.json().get('tx', {}).get('hash')
                
                if tx_hash:
                    logger.info(f"✅ Transaction broadcast: {tx_hash}")
                    return tx_hash
                else:
                    logger.error("No TX hash in response")
                    return None
                
            except Exception as e:
                logger.error(f"Transaction creation error: {e}", exc_info=True)
                return None
                
        except Exception as e:
            logger.error(f"Withdrawal error: {e}", exc_info=True)
            return None
    
    
    @staticmethod
    def sweep_to_master(
        from_address: str,
        private_key_wif: str,
        amount_ltc: float
    ) -> str:
        """
        Sweep entire balance from deposit address to master wallet
        
        Args:
            from_address: Source address (user deposit address)
            private_key_wif: Private key in WIF format
            amount_ltc: Amount to sweep in LTC
            
        Returns:
            Transaction hash or None
        """
        try:
            logger.info(f"Sweeping {amount_ltc:.8f} LTC from {from_address} to master wallet")
            
            # Use the withdraw method to send to master wallet
            return LitecoinSigner.withdraw(
                from_address=from_address,
                to_address=config.MASTER_WALLET_ADDRESS,
                amount=amount_ltc,
                private_key_wif=private_key_wif,
                use_rbf=False
            )
            
        except Exception as e:
            logger.error(f"Sweep error: {e}", exc_info=True)
            return None
