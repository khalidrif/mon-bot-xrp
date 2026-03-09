import ccxt
import time

# --- CONFIGURATION ---
exchange = ccxt.kraken()
symbol = 'XRP/USDC'

# 1. ENTRE TES DONNÉES ICI
prix_mon_achat = 2.40  # Le prix auquel tu as acheté tes XRP
quantite_detenue = 50  # Le nombre de XRP que tu as dans ton portefeuille

print(f"--- Surveillance du Profit pour {symbol} ---")
print(f"Prix d'achat : {prix_mon_achat} USDC | Quantité : {quantite_detenue}")

# --- LA BOUCLE DE SURVEILLANCE ---
while True:
    try:
        # 2. RÉCUPÈRE LE PRIX RÉEL
        ticker = exchange.fetch_ticker(symbol)
        prix_actuel = ticker['last']
        
        # 3. CALCULE LA VALEUR ACTUELLE ET LE PROFIT
        valeur_totale = prix_actuel * quantite_detenue
        profit_perte = valeur_totale - (prix_mon_achat * quantite_detenue)
        
        # 4. AFFICHE LE RÉSULTAT
        print(f"\nPrix Marché : {prix_actuel} USDC")
        print(f"Valeur actuelle de ton stock : {valeur_totale:.2f} USDC")
        
        if profit_perte > 0:
            print(f"✅ PROFIT : +{profit_perte:.2f} USDC 🚀")
        else:
            print(f"❌ PERTE : {profit_perte:.2f} USDC 📉")
            
    except Exception as e:
        print(f"Erreur : {e}")

    # 5. ATTENDS 10 SECONDES
    time.sleep(10)
