"""
Multi-node broadcast system for Litecoin transactions
Handles broadcasting to multiple blockchain nodes for reliability
"""

import requests
import logging
import time

logger = logging.getLogger('multi_broadcaster')

# List of public Litecoin nodes/APIs
BROADCAST_ENDPOINTS = [
    'https://api.blockcypher.com/v1/ltc/main/txs/push',  # BlockCypher
    'https://ltc.space/api/tx/send',  # LTC.space (if available)
]


def broadcast_transaction(tx_hex: str, tx_hash: str = None) -> dict:
    """
    Broadcast signed transaction to multiple nodes for redundancy
    Returns: {'success': bool, 'hash': str, 'node': str, 'error': str}
    """
    
    if not tx_hex or len(tx_hex) == 0:
        return {
            'success': False,
            'hash': None,
            'node': None,
            'error': 'Empty transaction hex'
        }
    
    logger.info(f"[BROADCAST] Attempting broadcast of TX with {len(tx_hex)} bytes")
    
    # Try each endpoint
    for endpoint in BROADCAST_ENDPOINTS:
        try:
            logger.debug(f"[BROADCAST] Trying {endpoint}")
            
            if 'blockcypher' in endpoint.lower():
                # BlockCypher format
                response = requests.post(
                    endpoint,
                    json={'tx': tx_hex},
                    timeout=10
                )
            else:
                # Generic format
                response = requests.post(
                    endpoint,
                    json={'txhex': tx_hex},
                    timeout=10
                )
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Extract tx hash from response
                result_hash = data.get('tx', {}).get('hash') or \
                             data.get('txid') or \
                             data.get('hash') or \
                             tx_hash
                
                logger.info(f"✅ [BROADCAST SUCCESS] Hash: {result_hash} via {endpoint}")
                
                return {
                    'success': True,
                    'hash': result_hash,
                    'node': endpoint,
                    'error': None
                }
            else:
                logger.warning(f"[BROADCAST] {endpoint} returned {response.status_code}: {response.text[:100]}")
                continue
                
        except requests.exceptions.Timeout:
            logger.warning(f"[BROADCAST] {endpoint} timeout")
            continue
        except requests.exceptions.ConnectionError:
            logger.warning(f"[BROADCAST] {endpoint} connection error")
            continue
        except Exception as e:
            logger.warning(f"[BROADCAST] {endpoint} failed: {str(e)[:100]}")
            continue
    
    # All endpoints failed
    logger.error(f"❌ [BROADCAST FAILED] Could not broadcast TX to any node")
    return {
        'success': False,
        'hash': tx_hash,
        'node': None,
        'error': 'All broadcast endpoints failed'
    }


def check_broadcast_status(tx_hash: str) -> dict:
    """
    Check if transaction was successfully broadcast and confirmed
    Returns: {'confirmed': bool, 'confirmations': int, 'status': str}
    """
    
    if not tx_hash:
        return {
            'confirmed': False,
            'confirmations': 0,
            'status': 'No transaction hash provided'
        }
    
    try:
        # Use BlockCypher to check status
        response = requests.get(
            f'https://api.blockcypher.com/v1/ltc/main/txs/{tx_hash}',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            confirmed = 'confirmed' in data and data['confirmed']
            confirmations = data.get('confirmations', 0)
            
            logger.debug(f"[BROADCAST] TX {tx_hash[:16]}... has {confirmations} confirmations")
            
            return {
                'confirmed': confirmed,
                'confirmations': confirmations,
                'status': 'confirmed' if confirmed else 'pending'
            }
        else:
            return {
                'confirmed': False,
                'confirmations': 0,
                'status': f'TX not found (HTTP {response.status_code})'
            }
            
    except Exception as e:
        logger.warning(f"[BROADCAST] Could not check TX status: {e}")
        return {
            'confirmed': False,
            'confirmations': 0,
            'status': f'Error checking status: {str(e)[:50]}'
        }


def broadcast_with_retry(tx_hex: str, max_retries: int = 3, tx_hash: str = None) -> dict:
    """
    Broadcast transaction with exponential backoff retry
    """
    
    for attempt in range(max_retries):
        try:
            result = broadcast_transaction(tx_hex, tx_hash)
            
            if result['success']:
                return result
            
            if attempt < max_retries - 1:
                # Exponential backoff: 2s, 4s, 8s
                wait_time = 2 ** (attempt + 1)
                logger.info(f"[BROADCAST] Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                
        except Exception as e:
            logger.error(f"[BROADCAST] Retry attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
    
    # All retries exhausted
    logger.error(f"[BROADCAST] Failed after {max_retries} attempts")
    return {
        'success': False,
        'hash': tx_hash,
        'node': None,
        'error': f'Failed after {max_retries} broadcast attempts'
    }
