# config.py
import ccxt

# REMPLACE PAR TES CLÉS RÉELLES
API_KEY = '2RXby/+ntL9pEZsOgfMeXSnGxYxntr59z+TxTcXJBlYDY+Ucz4M6f6N4'
SECRET_KEY = 'GPdLHKXJy2MQMzXn6KyjmqwYfkNHSTJvoCdV/oFuIntwCPbPVBC8QWYEBxPCAcvqLSfnx3/QqO+M6wD42Il0aA=='

def get_kraken_connection():
    """Configure la connexion sécurisée à Kraken."""
    return ccxt.kraken({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'enableRateLimit': True,
        'options': {'enableRateLimit': True}
    })
