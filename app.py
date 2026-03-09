import ccxt
import time
import json
import os

# --- CONFIGURATION ---
exchange = ccxt.kraken()
FICHIER_SIMU = "ordres_virtuels.json"
ECART_POURCENT = 0.005  # 0.5% pour voir plus de mouvements
MISE_PAR_TRADE = 10     # Simulation : on mise 10$ par opération

# Variables de statistiques
profit_total = 0.0
nombre_trades = 0

def charger_ordres():
    if os.path.exists(FICHIER_SIMU):
        with open(FICHIER_SIMU, 'r') as f:
            return json.load(f)
    return []

def sauvegarder_ordres(ordres):
    with open(FICHIER_SIMU, 'w') as f:
        json.dump(ordres, f, indent=4)

def afficher_interface(prix_reel, ordres):
    global profit_total, nombre_trades
    os.system('cls' if os.name == 'nt' else 'clear') # Nettoie l'écran
    
    print("="*50)
    print(f"       🤖 KRAKEN GRID BOT - SIMULATEUR 🤖")
    print("="*50)
    print(f" PRIX XRP ACTUEL : {prix_reel} $")
    print(f" TRADES RÉUSSIS  : {nombre_trades}")
    print(f" PROFIT ESTIMÉ   : {round(profit_total, 4)} $")
    print("-" * 50)
    print(" ORDRES ACTIFS EN ATTENTE :")
    
    actifs = [o for o in ordres if o['status'] == "open"]
    for o in actifs:
        type_ordre = "🟢 [ACHAT]" if o['side'] == "buy" else "🔴 [VENTE]"
        print(f"  {type_ordre} à {o['price']} $")
    
    if not actifs:
        print("  Aucun ordre actif...")
    print("="*50)
    print(" Appuyez sur Ctrl+C pour arrêter le bot.")

def simuler_bot_pro():
    global profit_total, nombre_trades
    
    # Initialisation de la grille au premier lancement
    if not charger_ordres():
        ticker = exchange.fetch_ticker('XRP/USDC')
        p = ticker['last']
        ordres = [
            {"side": "buy", "price": round(p * (1 - ECART_POURCENT), 4), "status": "open"},
            {"side": "sell", "price": round(p * (1 + ECART_POURCENT), 4), "status": "open"}
        ]
        sauvegarder_ordres(ordres)

    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_reel = ticker['last']
            ordres = charger_ordres()
            nouveaux_ordres = []
            a_sauvegarder = False

            for o in ordres:
                if o['status'] == "open":
                    # Détection ACHAT rempli
                    if o['side'] == "buy" and prix_reel <= o['price']:
                        o['status'] = "filled"
                        nombre_trades += 1
                        # On crée la vente pour prendre le profit
                        nouveaux_ordres.append({
                            "side": "sell", 
                            "price": round(o['price'] * (1 + ECART_POURCENT), 4), 
                            "status": "open"
                        })
                        a_sauvegarder = True
                    
                    # Détection VENTE remplie
                    elif o['side'] == "sell" and prix_reel >= o['price']:
                        o['status'] = "filled"
                        nombre_trades += 1
                        # Calcul du profit : (Prix Vente - Prix Achat théorique)
                        profit_total += (MISE_PAR_TRADE * ECART_POURCENT)
                        # On recrée un achat plus bas
                        nouveaux_ordres.append({
                            "side": "buy", 
                            "price": round(o['price'] * (1 - ECART_POURCENT), 4), 
                            "status": "open"
                        })
                        a_sauvegarder = True

            if a_sauvegarder:
                ordres.extend(nouveaux_ordres)
                sauvegarder_ordres(ordres)

            afficher_interface(prix_reel, ordres)
            time.sleep(5) # Mise à jour rapide toutes les 5 secondes

        except Exception as e:
            print(f"\n⚠️ Erreur : {e}")
            time.sleep(10)

if __name__ == "__main__":
    simuler_bot_pro()
