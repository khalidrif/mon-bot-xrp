import ccxt
import time
import os

# Connexion à Kraken (pense à définir tes variables d'environnement)
exchange = ccxt.kraken({
    'apiKey': os.getenv('KRAKEN_KEY'),
    'secret': os.getenv('KRAKEN_SECRET'),
    'enableRateLimit': True,
})

# --- PARAMÈTRES DU BOT ---
SYMBOL = 'XRP/USDC'
QUANTITE = 30       # Nombre de XRP à trader par opération
PROFIT_CIBLE = 0.02 # On veut 0.02 USDC de profit par XRP (ex: achat 1.30 -> vente 1.32)
# -------------------------

def bot_logic():
    print(f"=== Bot XRP lancé sur {SYMBOL} ===")
    
    while True:
        try:
            # 1. RÉCUPÉRER LE PRIX ACTUEL
            ticker = exchange.fetch_ticker(SYMBOL)
            prix_achat = ticker['last']
            prix_vente_cible = prix_achat + PROFIT_CIBLE

            # 2. ÉTAPE D'ACHAT (Market)
            print(f"Achat de {QUANTITE} XRP au prix de {prix_achat}...")
            # Commande réelle : 
            # order_buy = exchange.create_market_buy_order(SYMBOL, QUANTITE)
            print(f"Achat effectué ! Objectif de vente : {prix_vente_cible} USDC")

            # 3. BOUCLE D'ATTENTE DE REVENTE
            vendu = False
            while not vendu:
                ticker = exchange.fetch_ticker(SYMBOL)
                prix_actuel = ticker['last']
                print(f"Attente... Prix actuel : {prix_actuel} | Cible : {prix_vente_cible}")

                if prix_actuel >= prix_vente_cible:
                    print("Cible atteinte ! Vente en cours...")
                    # Commande réelle :
                    # order_sell = exchange.create_market_sell_order(SYMBOL, QUANTITE)
                    print("Vente terminée avec profit. Redémarrage du cycle.")
                    vendu = True
                
                time.sleep(20) # Vérifie le prix toutes les 20 secondes

        except Exception as e:
            print(f"Erreur rencontrée : {e}")
            time.sleep(60) # Attend 1 min avant de relancer en cas de bug

if __name__ == "__main__":
    bot_logic()
