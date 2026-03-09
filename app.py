import os
import time
import ccxt
import pandas_ta as ta
import pandas as pd

# 1. RÉCUPÉRATION DES SECRETS GITHUB
API_KEY = os.getenv('KRAKEN_API_KEY')
API_SECRET = os.getenv('KRAKEN_API_SECRET')

if not API_KEY or not API_SECRET:
    print("ERREUR: Les clés API ne sont pas configurées dans les GitHub Secrets.")
    exit()

# 2. CONFIGURATION DE KRAKEN
exchange = ccxt.kraken({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

# PARAMÈTRES DU BOT
SYMBOL = 'XRP/USDC'
STAKE_AMOUNT = 20.0    # Montant du premier achat en USDC
MULTIPLIER = 1.5       # On multiplie la mise par 1.5 à chaque palier de baisse
DIP_THRESHOLD = 0.02   # On rachete si le prix baisse de 2%
PROFIT_TARGET = 0.03   # On vend tout à +3% de profit global
STOP_LOSS = 0.15       # Sécurité : on coupe tout à -15% total

def get_price():
    ticker = exchange.fetch_ticker(SYMBOL)
    return ticker['last']

def get_balance(asset):
    balances = exchange.fetch_balance()
    return balances['free'].get(asset, 0)

def main():
    print(f"--- Lancement du Bot Boule de Neige XRP/USDC sur Kraken ---")
    
    in_position = False
    avg_price = 0
    total_spent = 0
    current_stake = STAKE_AMOUNT

    while True:
        try:
            price = get_price()
            
            # --- ÉTAPE 1 : ENTRÉE EN POSITION ---
            if not in_position:
                print(f"Prix actuel: {price} USDC. Premier achat de {STAKE_AMOUNT} USDC.")
                order = exchange.create_market_buy_order(SYMBOL, STAKE_AMOUNT / price)
                avg_price = price
                total_spent = STAKE_AMOUNT
                in_position = True
                print("Position ouverte.")

            # --- ÉTAPE 2 : SURVEILLANCE & EFFET BOULE DE NEIGE ---
            else:
                profit_pct = (price - avg_price) / avg_price
                
                # CAS A : TAKE PROFIT (On a gagné)
                if profit_pct >= PROFIT_TARGET:
                    print(f"Objectif atteint (+{profit_pct:.2%})! Vente totale.")
                    xrp_balance = get_balance('XRP')
                    exchange.create_market_sell_order(SYMBOL, xrp_balance)
                    in_position = False # Reset le cycle
                    current_stake = STAKE_AMOUNT # Reset la mise
                
                # CAS B : ACCUMULATION (Le prix baisse -> Boule de neige)
                elif profit_pct <= -DIP_THRESHOLD:
                    new_stake = current_stake * MULTIPLIER
                    print(f"Baisse détectée ({profit_pct:.2%}). Nouvel achat de {new_stake} USDC.")
                    exchange.create_market_buy_order(SYMBOL, new_stake / price)
                    
                    # Mise à jour du prix moyen (simplifiée)
                    total_spent += new_stake
                    avg_price = price 
                    current_stake = new_stake
                
                # CAS C : SÉCURITÉ (Stop Loss)
                elif profit_pct <= -STOP_LOSS:
                    print("Stop Loss déclenché. Vente d'urgence.")
                    xrp_balance = get_balance('XRP')
                    exchange.create_market_sell_order(SYMBOL, xrp_balance)
                    break

            time.sleep(60) # Vérification toutes les minutes

        except Exception as e:
            print(f"Erreur rencontrée : {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
