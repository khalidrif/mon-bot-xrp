import ccxt
import time
import os

def get_kraken_connection():
    # Récupère les clés depuis tes Secrets GitHub ou Variables d'environnement
    # Assure-toi que les noms correspondent (KRAKEN_KEY et KRAKEN_SECRET)
    api_key = os.getenv('KRAKEN_KEY') 
    api_secret = os.getenv('KRAKEN_SECRET')

    return ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True, # Évite d'être banni par Kraken pour trop de requêtes
        'options': {
            # Génère un numéro unique (nonce) basé sur les millisecondes
            'nonce': lambda: str(int(time.time() * 1000)) 
        }
    })
