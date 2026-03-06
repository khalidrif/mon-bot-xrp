import krakenex
import os

# CONFIGURATION
PAIR = 'XRPUSDC'      
ACHAT_USDC = 10       
PROFIT_CIBLE = 1.02   

k = krakenex.API(key=os.getenv('KRAKEN_KEY'), secret=os.getenv('KRAKEN_SECRET'))

def get_price(pair):
    res = k.query_public('Ticker', {'pair': pair})
    return float(res['result'][next(iter(res['result']))]['c'][0])

def main():
    try:
        prix_actuel = get_price(PAIR)
        print(f"🚀 Prix actuel du XRP: {prix_actuel} USDC")

        balance = k.query_private('Balance')['result']
        usdc_dispo = float(balance.get('USDC', 0))
        xrp_dispo = float(balance.get('XXRP', 0))
        print(f"💰 Portefeuille: {usdc_dispo} USDC | {xrp_dispo} XRP")

        # STRATÉGIE : Si on a + de 10 USDC, on achète du XRP
        if usdc_dispo >= ACHAT_USDC:
            print(f"🛒 Achat de {ACHAT_USDC} USDC en XRP...")
            volume = ACHAT_USDC / prix_actuel
            order = k.query_private('AddOrder', {
                'pair': PAIR,
                'type': 'buy',
                'ordertype': 'market',
                'volume': str(round(volume, 1))
            })
            print(order)
        
        # Si on a déjà du XRP (plus de 10 unités), on place une vente à +2%
        elif xrp_dispo > 10:
            prix_vente = prix_actuel * PROFIT_CIBLE
            print(f"🎯 Placement d'une vente à {prix_vente} USDC...")
            k.query_private('AddOrder', {
                'pair': PAIR,
                'type': 'sell',
                'ordertype': 'limit',
                'price': str(round(prix_vente, 5)),
                'volume': str(round(xrp_dispo, 1))
            })
        else:
            print("⏳ Solde USDC trop faible pour acheter.")

    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    main()
