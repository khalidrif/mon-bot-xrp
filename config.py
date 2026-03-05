import ccxt
import time

def get_kraken_connection():
    # RECOLLE TES CLÉS ICI (CELLES QUI FONCTIONNAIENT TOUT À L'HEURE)
    api_key = 'TA_CLE_API'.strip()
    api_secret = 'TON_SECRET_PRIVE'.strip()

    return ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'nonce': lambda: str(int(time.time() * 1000))
        }
    })
