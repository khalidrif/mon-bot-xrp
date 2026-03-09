import ccxt
import time
from datetime import datetime

# 1. CONNEXION (Remplace par tes vraies clés dans les Secrets)
import os
exchange = ccxt.kraken({
    'apiKey': os.getenv('KRAKEN_API_KEY'),
    'secret': os.getenv('KRAKEN_API_SECRET'),
})

symbol = 'XRP/USDC'

print(f"--- Mode Lecture Seule activé pour {symbol} ---")

# --- LA BOUCLE DE LECTURE ---
while True:
    try:
        # 2. LIRE LE PRIX DU MARCHÉ
        ticker = exchange.fetch_ticker(symbol)
        prix_actuel = ticker['last']
        
        # 3. LIRE TES SOLDES RÉELS
        balance = exchange.fetch_balance()
        mon_usdc = balance['free'].get('USDC', 0.0)
        mon_xrp = balance['free'].get('XRP', 0.0)
        
        # 4. AFFICHER LE RÉSULTAT
        heure = datetime.now().strftime("%H:%M:%S")
        print(f"[{heure}] Prix : {prix_actuel} USDC | Portefeuille : {mon_usdc:.2f} USDC / {mon_xrp:.2f} XRP")

    except Exception as e:
        print(f"Erreur de lecture : {e}")

    # 5. PAUSE DE 10 SECONDES
    time.sleep(10)
