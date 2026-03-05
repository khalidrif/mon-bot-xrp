import ccxt
import time

def get_kraken_connection():
    # REMPLACE LES TEXTES ENTRE GUILLEMETS PAR TES CLÉS RÉELLES
    api_key = 'TA_CLE_API_KRAKEN_ICI'.strip() 
    api_secret = 'TON_SECRET_KRAKEN_ICI_QUI_EST_TRES_LONG'.strip()

    return ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'nonce': lambda: str(int(time.time() * 1000)) 
        }
    })
