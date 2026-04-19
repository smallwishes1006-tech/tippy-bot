"""
Exchange rate utilities for Tippy Bot
Fetch LTC/USD rates and conversion functions with multiple fallbacks
"""

import requests
import logging
import time
import json
import os

logger = logging.getLogger('exchange_rates')

# Cache exchange rate for 30 minutes (longer cache to reduce API calls)
RATE_CACHE_SECONDS = 1800
CACHE_FILE = 'tippy_data/exchange_rate_cache.json'
_last_rate_fetch = 0
_cached_rate = 50.0  # Default fallback
_last_error_time = 0
_rate_limit_backoff = 0  # Exponential backoff counter
_retry_count = 0


def _load_cache_from_file():
    """Load exchange rate from disk cache (persistent across restarts)"""
    global _cached_rate, _last_rate_fetch
    
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                _cached_rate = data.get('rate', 50.0)
                _last_rate_fetch = data.get('timestamp', 0)
                logger.info(f"💾 Loaded cached rate from disk: ${_cached_rate:.2f}")
                return True
    except Exception as e:
        logger.debug(f"Could not load cache file: {e}")
    
    return False


def _save_cache_to_file(rate: float):
    """Save exchange rate to disk cache (persistent across restarts)"""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump({
                'rate': rate,
                'timestamp': time.time(),
                'source': 'tippy-bot'
            }, f)
        logger.debug(f"💾 Saved rate to cache: ${rate:.2f}")
    except Exception as e:
        logger.debug(f"Could not save cache file: {e}")


def _try_coingecko() -> float:
    """Try CoinGecko API"""
    try:
        response = requests.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={'ids': 'litecoin', 'vs_currencies': 'usd'},
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            rate = float(data.get('litecoin', {}).get('usd', 0))
            if rate > 0:
                logger.info(f"✅ CoinGecko: ${rate:.2f}")
                return rate
        elif response.status_code == 429:
            logger.warning("⏱️  CoinGecko rate limited (429)")
            return None
        else:
            logger.debug(f"CoinGecko error: {response.status_code}")
            return None
    except Exception as e:
        logger.debug(f"CoinGecko failed: {e}")
        return None


def _try_coinmarketcap() -> float:
    """Try CoinMarketCap API (free tier)"""
    try:
        response = requests.get(
            'https://api.coinmarketcap.com/data/v3.1/cryptocurrency/quotes/latest',
            params={'symbol': 'LTC', 'convert': 'USD'},
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            rate = data.get('data', {}).get('LTC', [{}])[0].get('quote', {}).get('USD', {}).get('price', 0)
            if rate > 0:
                logger.info(f"✅ CoinMarketCap: ${rate:.2f}")
                return rate
        else:
            logger.debug(f"CoinMarketCap error: {response.status_code}")
            return None
    except Exception as e:
        logger.debug(f"CoinMarketCap failed: {e}")
        return None


def _try_binance() -> float:
    """Try Binance API (public, no auth required)"""
    try:
        response = requests.get(
            'https://api.binance.com/api/v3/ticker/price',
            params={'symbol': 'LTCUSD'},
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            rate = float(data.get('price', 0))
            if rate > 0:
                logger.info(f"✅ Binance: ${rate:.2f}")
                return rate
        else:
            logger.debug(f"Binance error: {response.status_code}")
            return None
    except Exception as e:
        logger.debug(f"Binance failed: {e}")
        return None


def _try_kraken() -> float:
    """Try Kraken API"""
    try:
        response = requests.get(
            'https://api.kraken.com/0/public/Ticker',
            params={'pair': 'LTCUSD'},
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and 'LTCUSD' in data['result']:
                # Kraken returns [ask, bid, etc] arrays
                price = float(data['result']['LTCUSD']['c'][0])  # c = last trade
                if price > 0:
                    logger.info(f"✅ Kraken: ${price:.2f}")
                    return price
        else:
            logger.debug(f"Kraken error: {response.status_code}")
            return None
    except Exception as e:
        logger.debug(f"Kraken failed: {e}")
        return None


def get_ltc_usd_rate() -> float:
    """
    Get current LTC/USD rate with multiple API fallbacks
    Tries: CoinGecko → CoinMarketCap → Binance → Kraken → Cache → Default
    """
    global _last_rate_fetch, _cached_rate, _last_error_time, _rate_limit_backoff
    
    current_time = time.time()
    
    # If we hit rate limit, wait longer before retrying
    if _rate_limit_backoff > 0:
        if current_time - _last_error_time < _rate_limit_backoff:
            logger.debug(f"⏱️  Backoff active ({int(_rate_limit_backoff)}s), using cached: ${_cached_rate:.2f}")
            return _cached_rate
        else:
            logger.info("⏱️  Backoff expired, retrying APIs")
            _rate_limit_backoff = 0
    
    # Use cached rate if recent enough
    if current_time - _last_rate_fetch < RATE_CACHE_SECONDS:
        logger.debug(f"Cache valid, using: ${_cached_rate:.2f}")
        return _cached_rate
    
    logger.debug("Fetching fresh exchange rate...")
    
    # Try multiple APIs in order
    apis = [
        ("CoinGecko", _try_coingecko),
        ("CoinMarketCap", _try_coinmarketcap),
        ("Binance", _try_binance),
        ("Kraken", _try_kraken),
    ]
    
    for api_name, api_func in apis:
        try:
            rate = api_func()
            if rate and rate > 0:
                _cached_rate = rate
                _last_rate_fetch = current_time
                _rate_limit_backoff = 0
                _save_cache_to_file(rate)
                logger.info(f"✅ Exchange rate updated: ${rate:.2f} (from {api_name})")
                return rate
        except Exception as e:
            logger.debug(f"{api_name} exception: {e}")
            continue
    
    # All APIs failed - use cache
    logger.warning(f"⚠️  All APIs failed, using cached rate: ${_cached_rate:.2f}")
    
    # Implement exponential backoff to avoid hammering APIs
    _last_error_time = current_time
    _rate_limit_backoff = min(300, max(30, _rate_limit_backoff * 2 or 30))
    
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


# Initialize cache on module load
try:
    _load_cache_from_file()
    logger.info("✅ Exchange rate cache initialized")
except Exception as e:
    logger.warning(f"Could not initialize cache: {e}")
