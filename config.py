import ccxt
import time

def get_kraken_connection():
    # Remplace bien par tes vraies clés ici
    # .strip() sert à enlever les espaces accidentels
    api_key = 'TA_CLE_ICI'.strip() 
    api_secret = 'TON_SECRET_ICI'.strip()

    return ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'nonce': lambda: str(int(time.time() * 1000)) 
        }
    })
