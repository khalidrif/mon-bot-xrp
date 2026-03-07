import krakenex
import time

# --- CONFIGURATION API ---
k = krakenex.API()
k.key = 'VOTRE_CLE_API'      # <--- Colle ta clé API ici
k.secret = 'VOTRE_SECRET_API' # <--- Colle ton secret ici

PAIRE = 'XXRPZUSD'      # Paire XRP/Dollar
FRAIS_KRAKEN = 0.0026   # Frais de 0.26% par transaction

# --- CONFIGURATION INITIALE ---
print("="*45)
print("      BOT XRP BOULE DE NEIGE - FINAL")
print("="*45)
p_achat = float(input("Prix d'ACHAT cible (ex: 0.50)  : "))
p_vente = float(input("Prix de VENTE cible (ex: 0.55)  : "))
montant = float(input("Montant départ (Min 15 XRP) : "))

gain_net_cumule = 0.0
cycles = 0
etape = "ACHAT"

print(f"\n[STATUT] Bot lancé sur {PAIRE}...")
print(f"Stratégie : Acheter à {p_achat}$ / Vendre à {p_vente}$")
print("-" * 45)

while True:
    try:
        # 1. Récupération du prix actuel
        ticker = k.query_public('Ticker', {'pair': PAIRE})
        if ticker.get('error'):
            print(f"\nErreur API : {ticker['error']}")
            time.sleep(30)
            continue
            
        prix_actuel = float(ticker['result'][PAIRE]['c'][0])
        
        # 2. Affichage de la barre de statut dynamique
        barre = f"XRP: {prix_actuel:.4f}$ | FOURCHETTE: [{p_achat}$ - {p_vente}$] | MODE: {etape} | CYCLES: {cycles} | NET: +{gain_net_cumule:.2f}$"
        print(barre, end='\r')

        # 3. Logique d'ACHAT
        if etape == "ACHAT" and prix_actuel <= p_achat:
            print(f"\n[ACTION] Achat de {montant:.2f} XRP à {prix_actuel}$")
            
            # --- ACTIVER L'ORDRE REEL ICI ---
            # k.query_private('AddOrder', {'pair': PAIRE, 'type': 'buy', 'ordertype': 'market', 'volume': montant})
            
            etape = "VENTE"

        # 4. Logique de VENTE + CALCUL NET + REINVESTISSEMENT
        elif etape == "VENTE" and prix_actuel >= p_vente:
            print(f"\n[ACTION] Vente de {montant:.2f} XRP à {prix_actuel}$")
            
            # --- ACTIVER L'ORDRE REEL ICI ---
            # k.query_private('AddOrder', {'pair': PAIRE, 'type': 'sell', 'ordertype': 'market', 'volume': montant})

            # Calcul du profit NET (Vente - Achat - Frais des deux trades)
            valeur_vente = montant * prix_actuel
            valeur_achat = montant * p_achat
            frais_totaux = (valeur_vente + valeur_achat) * FRAIS_KRAKEN
            
            profit_net_cycle = valeur_vente - valeur_achat - frais_totaux
            gain_net_cumule += profit_net_cycle
            
            # EFFET BOULE DE NEIGE : On réinvestit le profit net pour le cycle suivant
            # On calcule combien d'XRP supplémentaires on peut acheter avec ce profit
            montant += (profit_net_cycle / prix_actuel)
            
            cycles += 1
            print(f"--- CYCLE N°{cycles} RÉUSSI ---")
            print(f"Gain Net Cycle : +{profit_net_cycle:.4f}$ | Total NET : {gain_net_cumule:.2f}$")
            print(f"Nouveau montant XRP pour le prochain cycle : {montant:.2f}")
            
            etape = "ACHAT"

    except Exception as e:
        print(f"\n[ERREUR] : {e}")
    
    # Pause de 10 secondes pour respecter les limites de Kraken
    time.sleep(10)
