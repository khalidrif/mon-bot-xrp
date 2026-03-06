import krakenex
import os

# CONFIGURATION DU BOT
PAIR = 'XRPUSDC'      # Paire de trading
ACHAT_USDC = 10       # Mise à chaque achat (en USDC)
PROFIT_CIBLE = 1.02   # Vendre à +2% profit

# Connexion API
k = krakenex.API(key=os.getenv('KRAKEN_KEY'), secret=os.getenv('KRAKEN_SECRET'))

def get_price(pair):
    res = k.query_public('Ticker', {'pair': pair})
    return float(res['result'][next(iter(res['result']))]['c'][0])

def main():
    prix_actuel = get_price(PAIR)
    print(f"🚀 Prix actuel du XRP: {prix_actuel} USDC")

    # 1. Vérifier le solde
    balance = k.query_private('Balance')['result']
    usdc_dispo = float(balance.get('USDC', 0))
    xrp_dispo = float(balance.get('XXRP', 0))

    print(f"💰 Portefeuille: {usdc_dispo} USDC | {xrp_dispo} XRP")

    # STRATÉGIE SIMPLE :
    # Si on a assez d'USDC, on achète un peu de XRP
    if usdc_dispo > ACHAT_USDC:
        print(f"🛒 Achat de {ACHAT_USDC} USDC en XRP...")
        order = k.query_private('AddOrder', {
            'pair': PAIR,
            'type': 'buy',
            'ordertype': 'market',
            'volume': str(ACHAT_USDC / prix_actuel)
        })
        print(order)
    
    # Si on a déjà du XRP, on place un ordre de vente avec profit (Limit Order)
    elif xrp_dispo > 10: # Seuil minimum pour vendre
        prix_vente = prix_actuel * PROFIT_CIBLE
        print(f"🎯 Placement d'une vente à {prix_vente} USDC...")
        order = k.query_private('AddOrder', {
            'pair': PAIR,
            'type': 'sell',
            'ordertype': 'limit',
            'price': str(round(prix_vente, 5)),
            'volume': str(xrp_dispo)
        })
        print(order)
    else:
        print("⏳ Rien à faire pour le moment.")

if __name__ == "__main__":
    main()
