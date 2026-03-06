import krakenex
import os

# CONFIGURATION
PAIR = 'XRPUSDC'      
ACHAT_USDC = 15  # Montant augmenté pour éviter les erreurs de minimum Kraken

k = krakenex.API(key=os.getenv('KRAKEN_KEY'), secret=os.getenv('KRAKEN_SECRET'))

def main():
    try:
        # 1. Récupérer le prix
        res = k.query_public('Ticker', {'pair': PAIR})
        prix = float(res['result'][next(iter(res['result']))]['c'][0])
        print(f"🚀 Prix actuel: {prix} USDC")

        # 2. Vérifier le solde
        bal = k.query_private('Balance')['result']
        usdc = float(bal.get('USDC', 0))
        print(f"💰 Solde: {usdc} USDC")

        # 3. Passer l'achat
        if usdc >= ACHAT_USDC:
            print(f"🛒 ACHAT DE {ACHAT_USDC} USDC en XRP...")
            volume = ACHAT_USDC / prix
            order = k.query_private('AddOrder', {
                'pair': PAIR,
                'type': 'buy',
                'ordertype': 'market',
                'volume': str(round(volume, 1))
            })
            print(f"✅ RÉSULTAT : {order}")
        else:
            print("❌ Pas assez d'USDC pour acheter.")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    main()
