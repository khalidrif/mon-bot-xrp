import ccxt
import time

def get_kraken_connection():
    # MÉTHODE DIRECTE (TES CLÉS SONT ÉCRITES ICI)
    api_key = "xbTqkWHQt+9dm8zGsNVK4H6tyUlzmkOH2Tadvxfv9BITwtnavVnAJeCX".strip()
    api_secret = "r7IN4tCkb5wNg6C1Aa62jmtxn3JoB4kkqL9NDynBi9pfLzo0IA2hUccX68fUdI3F8CoWoUZZuhpBghpv6lSCUQ==".strip()

    exchange = ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'nonce': lambda: int(time.time() * 1000)}
    })
    
    # Force le chargement pour éviter l'erreur "Markets not loaded"
    exchange.load_markets()
    return exchange

