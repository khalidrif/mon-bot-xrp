import krakenex
import os

# CONFIGURATION
PAIR = 'XRPUSDC'      
ACHAT_USDC = 20  

k = krakenex.API(key=os.getenv('KRAKEN_KEY'), secret=os.getenv('KRAKEN_SECRET'))

def main():
    try:
        print("🚀 DEBUT DU BOT KRAKEN...")
        res = k.query_public('Ticker', {'pair': PAIR})
        
        # CORRECTION ICI : On prend le premier élément [0] de la liste 'c'
        infos_paire = res['result'][next(iter(res['result']))]
        prix = float(infos_paire['c'][0]) 
        
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
            print(f"✅ REPONSE KRAKEN : {order}")
        else:
            print("❌ SOLDE TROP FAIBLE")
            
    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    main()
