"""
Exchange rate utilities for Tippy Bot
Fetch LTC/USD rates and conversion functions
"""

import requests
import logging
import time

logger = logging.getLogger('exchange_rates')

# Cache exchange rate for 10 minutes (increased from 5 to reduce API calls)
RATE_CACHE_SECONDS = 600
_last_rate_fetch = 0
_cached_rate = 50.0  # Default fallback
_last_error_time = 0
_rate_limit_backoff = 0  # Exponential backoff counter


def get_ltc_usd_rate() -> float:
    """
    Get current LTC/USD rate from CoinGecko API
    Falls back to cached rate if API fails or rate-limited
    Implements exponential backoff for 429 errors
    """
    global _last_rate_fetch, _cached_rate, _last_error_time, _rate_limit_backoff
    
    current_time = time.time()
    
    # If we hit rate limit, wait longer before retrying (exponential backoff)
    if _rate_limit_backoff > 0:
        if current_time - _last_error_time < _rate_limit_backoff:
            logger.debug(f"Rate limit backoff active for {_rate_limit_backoff}s, using cached rate")
            return _cached_rate
        else:
            logger.info("Rate limit backoff expired, retrying API")
            _rate_limit_backoff = 0
    
    # Use cached rate if less than RATE_CACHE_SECONDS old
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
            _rate_limit_backoff = 0  # Reset backoff on success
            logger.debug(f"✅ Updated LTC/USD rate: ${rate:.2f}")
            return rate
        
        elif response.status_code == 429:
            # Rate limited - implement exponential backoff
            _last_error_time = current_time
            _rate_limit_backoff = min(300, max(30, _rate_limit_backoff * 2 or 30))  # 30-300s backoff
            logger.warning(f"⏱️  CoinGecko rate limit (429). Backing off for {_rate_limit_backoff}s. Using cached rate: ${_cached_rate:.2f}")
            return _cached_rate
        
        else:
            logger.warning(f"⚠️  CoinGecko API error: {response.status_code}. Using cached rate: ${_cached_rate:.2f}")
            return _cached_rate
            
    except requests.Timeout:
        logger.warning(f"⏱️  CoinGecko API timeout. Using cached rate: ${_cached_rate:.2f}")
        return _cached_rate
        
    except Exception as e:
        logger.warning(f"⚠️  Could not fetch exchange rate: {e}. Using cached rate: ${_cached_rate:.2f}")
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
