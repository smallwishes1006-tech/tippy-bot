"""
Exchange rate utilities for Tippy Bot
Fetch LTC/USD rates and conversion functions
"""

import requests
import logging
from functools import lru_cache
import time

logger = logging.getLogger('exchange_rates')

# Cache exchange rate for 5 minutes
RATE_CACHE_SECONDS = 300
_last_rate_fetch = 0
_cached_rate = 50.0  # Default fallback


@lru_cache(maxsize=1)
def get_ltc_usd_rate() -> float:
    """
    Get current LTC/USD rate from CoinGecko API
    Falls back to cached rate if API fails
    """
    global _last_rate_fetch, _cached_rate
    
    current_time = time.time()
    
    # Use cached rate if less than 5 minutes old
    if current_time - _last_rate_fetch < RATE_CACHE_SECONDS:
        return _cached_rate
    
    try:
        response = requests.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={'ids': 'litecoin', 'vs_currencies': 'usd'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            rate = float(data.get('litecoin', {}).get('usd', _cached_rate))
            _cached_rate = rate
            _last_rate_fetch = current_time
            logger.debug(f"Updated LTC/USD rate: ${rate:.2f}")
            return rate
        else:
            logger.warning(f"CoinGecko API error: {response.status_code}")
            return _cached_rate
            
    except Exception as e:
        logger.warning(f"Could not fetch exchange rate: {e}, using cached: ${_cached_rate:.2f}")
        return _cached_rate


def ltc_to_usd(ltc_amount: float) -> float:
    """Convert LTC amount to USD"""
    rate = get_ltc_usd_rate()
    return ltc_amount * rate


def usd_to_ltc(usd_amount: float) -> float:
    """Convert USD amount to LTC"""
    rate = get_ltc_usd_rate()
    if rate == 0:
        return 0
    return usd_amount / rate


def format_amount(ltc_amount: float, usd_amount: float = None) -> str:
    """
    Format amount for display
    Shows both LTC and USD if USD provided
    """
    if usd_amount is None:
        usd_amount = ltc_to_usd(ltc_amount)
    
    return f"**{ltc_amount:.8f}** LTC (~**${usd_amount:.2f}**)"
