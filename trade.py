import krakenex
import os

# --- CONFIGURATION DE LA GRILLE ---
PAIR = 'XRPUSDC'      
MONTANT_ACHAT = 15    # Somme misée à chaque palier (USDC)
PROFIT_CIBLE = 1.02   # On revend à +2% (1.02)

k = krakenex.API(key=os.getenv('KRAKEN_KEY'), secret=os.getenv('KRAKEN_SECRET'))

def main():
    try:
        # 1. Récupérer le prix actuel
        res_ticker = k.query_public('Ticker', {'pair': PAIR})
        prix_actuel = float(res_ticker['result'][next(iter(res_ticker['result']))]['c'][0])
        print(f"🚀 Prix actuel du XRP: {prix_actuel} USDC")

        # 2. Vérifier les soldes
        bal = k.query_private('Balance')['result']
        usdc_dispo = float(bal.get('USDC', 0))
        xrp_dispo = float(bal.get('XXRP', 0))
        print(f"💰 Solde: {usdc_dispo:.2f} USDC | {xrp_dispo:.2f} XRP")

        # 3. Vérifier s'il y a déjà des ordres de vente ou d'achat ouverts
        open_orders = k.query_private('OpenOrders')['result']['open']
        
        if open_orders:
            print(f"⏳ {len(open_orders)} ordre(s) déjà en attente sur Kraken. On attend.")
            return

        # 4. LOGIQUE DE LA GRILLE
        # SI on a assez d'USDC -> On achète une tranche de XRP au prix du marché
        if usdc_dispo >= MONTANT_ACHAT:
            print(f"🛒 Grille : Achat de {MONTANT_ACHAT} USDC...")
            volume = MONTANT_ACHAT / prix_actuel
            res_buy = k.query_private('AddOrder', {
                'pair': PAIR, 'type': 'buy', 'ordertype': 'market', 'volume': str(round(volume, 1))
            })
            print(f"✅ Achat effectué : {res_buy.get('result', {}).get('txid')}")

            # Immédiatement après l'achat, on calcule le prix de vente (+2%)
            prix_vente = prix_actuel * PROFIT_CIBLE
            print(f"🎯 Placement de la vente automatique à {prix_vente:.5f} USDC...")
            res_sell = k.query_private('AddOrder', {
                'pair': PAIR, 'type': 'sell', 'ordertype': 'limit', 
                'price': str(round(prix_vente, 5)), 'volume': str(round(volume, 1))
            })
            print(f"📦 Ordre de vente placé : {res_sell.get('result', {}).get('txid')}")

        else:
            print("❌ Pas assez d'USDC pour un nouvel achat.")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    main()
