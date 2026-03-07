import krakenex
import time

# --- CONFIGURATION API ---
k = krakenex.API()
k.key = 'VOTRE_CLE_API'
k.secret = 'VOTRE_SECRET_API'

# Paire XRP/USDC sur Kraken
PAIRE = 'XRPUSDC' 
FRAIS_KRAKEN = 0.0026 # 0.26% par transaction

# --- CONFIGURATION INITIALE ---
print("="*45)
print("   BOT XRP/USDC - BOULE DE NEIGE")
print("="*45)
p_achat = float(input("Prix d'ACHAT cible (en USDC) : "))
p_vente = float(input("Prix de VENTE cible (en USDC) : "))

# Paramètres demandés : 20 XRP au départ
montant_actuel = 20.00
gain_net_cumule = 0.0
cycles = 0
etape = "ACHAT" # Le bot attend que le prix baisse pour racheter

print(f"\n[DÉMARRAGE] Stock initial : {montant_actuel} XRP")
print(f"Cibles : [{p_achat} USDC <-> {p_vente} USDC]")
print("-" * 45)

while True:
    try:
        # 1. Récupération du prix XRP/USDC
        ticker = k.query_public('Ticker', {'pair': PAIRE})
        if ticker.get('error'):
            print(f"\nErreur API : {ticker['error']}")
            time.sleep(30)
            continue
            
        # Kraken utilise souvent des noms de paires spécifiques dans le dictionnaire de réponse
        # Pour XRP/USDC, la clé est généralement 'XRPUSDC'
        res_pair = list(ticker['result'].keys())[0]
        prix_reel = float(ticker['result'][res_pair]['c'][0])
        
        # 2. Affichage de la barre de statut
        stats = f"XRP: {prix_reel:.4f} USDC | [{p_achat} <-> {p_vente}] | Mode: {etape} | Cycles: {cycles} | NET: +{gain_net_cumule:.2f} USDC"
        print(stats, end='\r')

        # 3. Logique d'ACHAT
        if etape == "ACHAT" and prix_reel <= p_achat:
            print(f"\n[ACTION] Achat de {montant_actuel:.2f} XRP à {prix_reel} USDC")
            # k.query_private('AddOrder', {'pair': PAIRE, 'type': 'buy', 'ordertype': 'market', 'volume': montant_actuel})
            etape = "VENTE"

        # 4. Logique de VENTE + BOULE DE NEIGE
        elif etape == "VENTE" and prix_reel >= p_vente:
            print(f"\n[ACTION] Vente de {montant_actuel:.2f} XRP à {prix_reel} USDC")
            # k.query_private('AddOrder', {'pair': PAIRE, 'type': 'sell', 'ordertype': 'market', 'volume': montant_actuel})

            # Calcul du profit NET (Vente - Achat - Frais des deux trades)
            v_vente = montant_actuel * prix_reel
            v_achat = montant_actuel * p_achat
            frais = (v_vente + v_achat) * FRAIS_KRAKEN
            
            p_net = v_vente - v_achat - frais
            gain_net_cumule += p_net
            
            # RÉINVESTISSEMENT (Boule de neige)
            # On transforme le gain net USDC en XRP supplémentaires pour le prochain tour
            montant_actuel += (p_net / prix_reel)
            
            cycles += 1
            print(f"--- CYCLE N°{cycles} RÉUSSI ---")
            print(f"Gain Cycle : +{p_net:.4f} USDC | Total NET : {gain_net_cumule:.2f} USDC")
            print(f"Nouveau Stock : {montant_actuel:.2f} XRP")
            etape = "ACHAT"

    except Exception as e:
        print(f"\n[ERREUR] : {e}")
    
    time.sleep(10)
