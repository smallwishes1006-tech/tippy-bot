import sys, logging
sys.path.insert(0, '.')
logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')

print('[CHECK] Loading all modules...')
import config; print('[?] config')
import address_validator; print('[?] address_validator')
import exchange_rates; print('[?] exchange_rates')
import tippy_system; print('[?] tippy_system')
import litecoin_signer; print('[?] litecoin_signer')
import tippy_commands; print('[?] tippy_commands')
import bot_main; print('[?] bot_main')

print()
print('[CHECK] Testing core functions...')
rate = exchange_rates.get_ltc_usd_rate()
print(f'[?] Exchange rate: ${rate:.2f}')

user = tippy_system.get_user_account(123456)
print(f'[?] User account: {user.deposit_address[:20]}...')

addr = address_validator.LitecoinValidator.validate_address('LgtpifMGDFirYSp39esx3zb4v47KgqubBk')
print(f'[?] Address validation: {addr}')

print()
print('[SUCCESS] All systems ready!')
