import ccxt
import time

def get_kraken_connection():
    # REMPLACE LES VALEURS CI-DESSOUS PAR TES VRAIES CLÉS KRAKEN
    api_key = 'TA_CLE_API_ICI' 
    api_secret = 'TON_SECRET_API_ICI'

    return ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'nonce': lambda: str(int(time.time() * 1000)) 
        }
    })
