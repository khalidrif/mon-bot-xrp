import krakenex
import os

# CONFIGURATION
PAIR = 'XRPUSDC'      
ACHAT_USDC = 20  # Montant pour le test (un peu plus haut pour Kraken)

k = krakenex.API(key=os.getenv('KRAKEN_KEY'), secret=os.getenv('KRAKEN_SECRET'))

def main():
    try:
        print("🚀 DEBUT DU BOT KRAKEN...")
        res = k.query_public('Ticker', {'pair': PAIR})
        prix = float(res['result'][next(iter(res['result']))]['c'])
        print(f"📈 Prix XRP: {prix} USDC")

        bal = k.query_private('Balance')['result']
        usdc_dispo = float(bal.get('USDC', 0))
        print(f"💰 Solde dispo: {usdc_dispo} USDC")

        if usdc_dispo >= ACHAT_USDC:
            print(f"🛒 ORDRE D'ACHAT DE {ACHAT_USDC} USDC...")
            volume = ACHAT_USDC / prix
            order = k.query_private('AddOrder', {
                'pair': PAIR,
                'type': 'buy',
                'ordertype': 'market',
                'volume': str(round(volume, 1))
            })
            print(f"✅ REPONSE : {order}")
        else:
            print("❌ SOLDE TROP FAIBLE")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    main()
