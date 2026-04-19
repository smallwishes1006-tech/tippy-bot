"""
Exchange rate utilities for Tippy Bot
Fetch LTC/USD rates and conversion functions with multiple fallbacks
Includes smart rate limiting and retry logic
"""

import requests
import logging
import time
import json
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger('exchange_rates')

# Cache exchange rate for 20 minutes (reduced to get fresher rates)
RATE_CACHE_SECONDS = 1200
CACHE_FILE = 'tippy_data/exchange_rate_cache.json'
_last_rate_fetch = 0
_cached_rate = 50.0  # Default fallback
_last_error_time = 0
_rate_limit_backoff = 0  # Exponential backoff counter
_retry_count = 0

# Session with retry strategy for HTTP requests
def _get_session():
    """Create requests session with automatic retries"""
    session = requests.Session()
    retry_strategy = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


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
    """Try CoinGecko API with proper headers and timeouts"""
    try:
        session = _get_session()
        response = session.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={'ids': 'litecoin', 'vs_currencies': 'usd'},
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (TippyBot/1.0)',
                'Accept': 'application/json'
            },
            timeout=8
        )
        
        if response.status_code == 200:
            data = response.json()
            rate = float(data.get('litecoin', {}).get('usd', 0))
            if rate > 0:
                logger.info(f"✅ CoinGecko: ${rate:.2f}")
                return rate
        elif response.status_code == 429:
            logger.warning("⏱️  CoinGecko rate limited (429) - backing off")
            return None
        else:
            logger.debug(f"CoinGecko error: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        logger.debug("CoinGecko timeout")
        return None
    except Exception as e:
        logger.debug(f"CoinGecko failed: {e}")
        return None


def _try_coinmarketcap() -> float:
    """Try CoinMarketCap API (free alternative via public source)"""
    try:
        time.sleep(0.3)  # Rate limit protection
        session = _get_session()
        response = session.get(
            'https://web-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
            params={'symbol': 'LTC', 'convert': 'USD'},
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (TippyBot/1.0)',
                'Accept': 'application/json'
            },
            timeout=8
        )
        
        if response.status_code == 200:
            data = response.json()
            ltc_data = data.get('data', {}).get('LTC', {})
            price = ltc_data.get('quote', {}).get('USD', {}).get('price', 0)
            if price > 0:
                logger.info(f"✅ CoinMarketCap: ${price:.2f}")
                return price
        elif response.status_code == 429:
            logger.warning("⏱️  CoinMarketCap rate limited (429)")
            return None
        else:
            logger.debug(f"CoinMarketCap error: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        logger.debug("CoinMarketCap timeout")
        return None
    except Exception as e:
        logger.debug(f"CoinMarketCap failed: {e}")
        return None


def _try_binance() -> float:
    """Try Binance API (public, no auth required)"""
    try:
        time.sleep(0.3)  # Rate limit protection
        session = _get_session()
        response = session.get(
            'https://api.binance.com/api/v3/ticker/price',
            params={'symbol': 'LTCUSDT'},
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (TippyBot/1.0)',
                'Accept': 'application/json'
            },
            timeout=8
        )
        
        if response.status_code == 200:
            data = response.json()
            rate = float(data.get('price', 0))
            if rate > 0:
                logger.info(f"✅ Binance: ${rate:.2f}")
                return rate
        elif response.status_code == 429:
            logger.warning("⏱️  Binance rate limited (429)")
            return None
        else:
            logger.debug(f"Binance error: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        logger.debug("Binance timeout")
        return None
    except Exception as e:
        logger.debug(f"Binance failed: {e}")
        return None


def _try_kraken() -> float:
    """Try Kraken API"""
    try:
        time.sleep(0.3)  # Rate limit protection
        session = _get_session()
        response = session.get(
            'https://api.kraken.com/0/public/Ticker',
            params={'pair': 'XLTCZUSD'},
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (TippyBot/1.0)',
                'Accept': 'application/json'
            },
            timeout=8
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and data['result']:
                # Get first key in result (pair name)
                pair_key = list(data['result'].keys())[0]
                price_data = data['result'][pair_key]
                # c = last trade price [price, lot volume]
                if 'c' in price_data:
                    price = float(price_data['c'][0])
                    if price > 0:
                        logger.info(f"✅ Kraken: ${price:.2f}")
                        return price
            logger.debug(f"Kraken: No valid data in response")
            return None
        elif response.status_code == 429:
            logger.warning("⏱️  Kraken rate limited (429)")
            return None
        else:
            logger.debug(f"Kraken error: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        logger.debug("Kraken timeout")
        return None
    except Exception as e:
        logger.debug(f"Kraken failed: {e}")
        return None


def get_ltc_usd_rate() -> float:
    """
    Get current LTC/USD rate with multiple API fallbacks
    Tries: CoinGecko → CoinMarketCap → Binance → Kraken → Cache → Default
    Implements intelligent backoff and retry logic
    
    CRITICAL: Always returns rate > 0 (raises exception if unavailable)
    """
    global _last_rate_fetch, _cached_rate, _last_error_time, _rate_limit_backoff
    
    current_time = time.time()
    
    # If we hit rate limit, implement exponential backoff
    if _rate_limit_backoff > 0:
        time_since_error = current_time - _last_error_time
        if time_since_error < _rate_limit_backoff:
            remaining = int(_rate_limit_backoff - time_since_error)
            logger.debug(f"⏱️  Backoff active ({remaining}s), using cached: ${_cached_rate:.2f}")
            # Validate cached rate
            if _cached_rate <= 0:
                logger.error(f"[CRITICAL] Cached rate invalid: {_cached_rate}")
                raise ValueError("Exchange rate unavailable")
            return _cached_rate
        else:
            logger.info("⏱️  Backoff expired, retrying APIs")
            _rate_limit_backoff = 0
    
    # Use cached rate if recent enough (20 minute cache)
    if current_time - _last_rate_fetch < RATE_CACHE_SECONDS:
        logger.debug(f"Cache valid ({int(RATE_CACHE_SECONDS - (current_time - _last_rate_fetch))}s left), using: ${_cached_rate:.2f}")
        # Validate cached rate
        if _cached_rate <= 0:
            logger.error(f"[CRITICAL] Cached rate invalid: {_cached_rate}")
            raise ValueError("Exchange rate unavailable")
        return _cached_rate
    
    logger.info("🔄 Fetching fresh exchange rate...")
    
    # Try multiple APIs in order with delays
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
                _rate_limit_backoff = 0  # Reset backoff on success
                _save_cache_to_file(rate)
                logger.info(f"✅ Exchange rate updated: ${rate:.2f} (from {api_name})")
                return rate
            time.sleep(0.5)  # Delay between API attempts
        except Exception as e:
            logger.debug(f"{api_name} exception: {e}")
            time.sleep(0.5)
            continue
    
    # All APIs failed - use cache with backoff
    logger.warning(f"⚠️  All APIs failed, using cached rate: ${_cached_rate:.2f}")
    
    # Validate cached rate - if invalid, raise error
    if _cached_rate <= 0:
        logger.error(f"[CRITICAL] Cached rate invalid after API failure: {_cached_rate} - rejecting")
        raise ValueError("Exchange rate unavailable - cannot proceed")
    
    # Implement exponential backoff: 30s → 60s → 120s → 300s (max 5 min)
    _last_error_time = current_time
    if _rate_limit_backoff == 0:
        _rate_limit_backoff = 30
    else:
        _rate_limit_backoff = min(300, _rate_limit_backoff * 2)
    
    logger.info(f"⏱️  Next retry in {int(_rate_limit_backoff)} seconds")
    
    return _cached_rate


def ltc_to_usd(ltc_amount: float) -> float:
    """Convert LTC amount to USD
    
    CRITICAL: Validates rate > 0 to prevent free withdrawals
    """
    rate = get_ltc_usd_rate()
    
    # Validation: prevent zero/negative rates
    if not rate or rate <= 0:
        logger.error(f"[CRITICAL] Invalid exchange rate: {rate} - refusing calculation")
        raise ValueError("Exchange rate unavailable - cannot calculate fee")
    
    if ltc_amount < 0:
        logger.error(f"[CRITICAL] Negative LTC amount: {ltc_amount}")
        raise ValueError("Amount cannot be negative")
    
    result = ltc_amount * rate
    logger.debug(f"[RATE] Converted {ltc_amount:.8f} LTC to ${result:.2f}")
    return result


def usd_to_ltc(usd_amount: float) -> float:
    """Convert USD amount to LTC
    
    CRITICAL: Validates rate > 0 to prevent miscalculations
    """
    rate = get_ltc_usd_rate()
    
    # Validation: prevent zero/negative rates
    if not rate or rate <= 0:
        logger.error(f"[CRITICAL] Invalid exchange rate: {rate} - refusing calculation")
        raise ValueError("Exchange rate unavailable - cannot calculate amount")
    
    if usd_amount < 0:
        logger.error(f"[CRITICAL] Negative USD amount: {usd_amount}")
        raise ValueError("Amount cannot be negative")
    
    if rate == 0:
        logger.error("[CRITICAL] Exchange rate is zero")
        return 0
    
    result = usd_amount / rate
    logger.debug(f"[RATE] Converted ${usd_amount:.2f} to {result:.8f} LTC")
    return result


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
