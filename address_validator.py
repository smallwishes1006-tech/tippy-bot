"""
Address validation for Litecoin
Verifies that addresses are valid before broadcasting transactions
"""

import hashlib
import logging

logger = logging.getLogger('address_validator')


class LitecoinValidator:
    """Validate Litecoin addresses"""
    
    # Base58 characters used in Bitcoin/Litecoin addresses
    BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    
    @staticmethod
    def decode_base58(address: str) -> bytes:
        """Decode a Base58 encoded string"""
        decoded = 0
        multi = 1
        
        for char in reversed(address):
            if char not in LitecoinValidator.BASE58_ALPHABET:
                return None
            decoded += multi * LitecoinValidator.BASE58_ALPHABET.index(char)
            multi *= 58
        
        return decoded.to_bytes(25, byteorder='big')
    
    @staticmethod
    def validate_address(address: str) -> bool:
        """
        Validate a Litecoin address
        Checks: format, length, checksum, network byte
        
        Supports:
        - Legacy P2PKH (L prefix) - mainnet
        - Legacy P2PKH (m/n prefix) - testnet
        - P2SH (M prefix) - mainnet
        - P2SH (2 prefix) - testnet
        - Bech32 (ltc1 prefix) - mainnet
        - Bech32 (tltc1 prefix) - testnet
        """
        
        if not address or not isinstance(address, str):
            return False
        
        # Check for Bech32 format (ltc1 or tltc1)
        if address.startswith('ltc1') or address.startswith('tltc1'):
            return LitecoinValidator._validate_bech32(address)
        
        # Check for legacy format (Base58Check)
        if len(address) < 26 or len(address) > 35:
            return False
        
        # Decode Base58
        try:
            decoded = LitecoinValidator.decode_base58(address)
            if decoded is None or len(decoded) != 25:
                return False
        except:
            return False
        
        # Split into payload and checksum
        payload = decoded[:21]
        checksum = decoded[21:]
        
        # Calculate expected checksum
        hash_result = hashlib.sha256(hashlib.sha256(payload).digest()).digest()
        expected_checksum = hash_result[:4]
        
        if checksum != expected_checksum:
            logger.warning(f"Invalid checksum for address: {address}")
            return False
        
        # Check network byte (first byte of payload)
        version_byte = payload[0]
        
        # Litecoin mainnet: 0x30 (L prefix) or 0x05 (M prefix)
        # Litecoin testnet: 0x6f (m/n prefix) or 0xc4 (2 prefix)
        valid_mainnet_bytes = [0x30, 0x05]  # L and M
        valid_testnet_bytes = [0x6f, 0xc4]  # m/n and 2
        
        if version_byte not in valid_mainnet_bytes + valid_testnet_bytes:
            logger.warning(f"Invalid network byte for address: {address}")
            return False
        
        return True
    
    @staticmethod
    def _validate_bech32(address: str) -> bool:
        """Validate Bech32 encoded Litecoin address (ltc1/tltc1)"""
        try:
            # Basic format check
            if not (address.startswith('ltc1') or address.startswith('tltc1')):
                return False
            
            # Check length (Bech32 addresses are typically 42-62 chars)
            if len(address) < 42 or len(address) > 62:
                return False
            
            # Lowercase check
            if address != address.lower():
                return False
            
            # Check for invalid characters
            valid_chars = set('023456789acdefghjklmnpqrstuvwxyz')
            if not all(c in valid_chars for c in address[4:]):  # Skip hrp
                return False
            
            return True
        except:
            return False
    
    @staticmethod
    def get_address_type(address: str) -> str:
        """Return the type of Litecoin address"""
        if not LitecoinValidator.validate_address(address):
            return "invalid"
        
        if address.startswith('ltc1'):
            return "segwit_mainnet"
        elif address.startswith('tltc1'):
            return "segwit_testnet"
        elif address.startswith('L'):
            return "p2pkh_mainnet"
        elif address.startswith('M'):
            return "p2sh_mainnet"
        elif address.startswith(('m', 'n')):
            return "p2pkh_testnet"
        elif address.startswith('2'):
            return "p2sh_testnet"
        else:
            return "unknown"
