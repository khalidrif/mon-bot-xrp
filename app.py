import ccxt
import time

# Connexion à Kraken
exchange = ccxt.kraken({
    'apiKey': 'VOTRE_CLE_API',
    'secret': 'VOTRE_SECRET_API',
    'enableRateLimit': True,
})

symbol = 'XRP/USDC'
initial_stake = 20  # Premier achat de 20 USDC
multiplier = 1.5    # Facteur multiplicateur pour chaque palier suivant
price_step = 0.02   # Acheter de nouveau si le prix baisse de 2%

def get_balance(asset):
    return exchange.fetch_balance()['free'].get(asset, 0)

def run_snowball_cycle():
    print(f"Démarrage d'un cycle sur {symbol}")
    
    # 1. Premier achat
    order = exchange.create_market_buy_order(symbol, initial_stake / exchange.fetch_ticker(symbol)['last'])
    last_buy_price = order['price'] or exchange.fetch_ticker(symbol)['last']
    current_stake = initial_stake
    
    while True:
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Calcul du profit actuel (moyenne simplifiée)
        # Note : Dans un bot réel, calculez précisément le 'break-even'
        
        # CONDITION DE VENTE (Take Profit à +3%)
        if current_price > last_buy_price * 1.03:
            print("Objectif atteint ! Vente de tout le stock.")
            balance_xrp = get_balance('XRP')
            exchange.create_market_sell_order(symbol, balance_xrp)
            break # Fin du cycle, on recommence
            
        # CONDITION D'ACHAT (Effet boule de neige si baisse de 2%)
        elif current_price < last_buy_price * (1 - price_step):
            new_stake = current_stake * multiplier
            print(f"Baisse détectée. Achat supplémentaire de {new_stake} USDC")
            exchange.create_market_buy_order(symbol, new_stake / current_price)
            last_buy_price = current_price
            current_stake = new_stake
            
        time.sleep(30) # Attendre 30 secondes

while True:
    try:
        run_snowball_cycle()
    except Exception as e:
        print(f"Erreur : {e}")
        time.sleep(60)
