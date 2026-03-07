import time
import krakenex

api = krakenex.API()
api.load_key('kraken.key')

def get_price():
    data = api.query_public('Ticker', {'pair': 'XRPUSD'})
    return float(data['result']['XXRPZUSD']['c'][0])

def place_order(order_type, volume):
    return api.query_private('AddOrder', {
        'pair': 'XRPUSD',
        'type': order_type,
        'ordertype': 'market',
        'volume': volume
    })

prix_achat = float(input("Prix d'achat (USD) : "))
prix_vente = float(input("Prix de vente (USD) : "))
montant = float(input("Montant en XRP : "))

position = 0

print("\nBot XRP Kraken lancé...")
print("-----------------------------------\n")

while True:
    prix = get_price()
    print("Prix actuel XRP :", prix)

    if position == 0 and prix <= prix_achat:
        print(">>> Achat de", montant, "XRP")
        print(place_order("buy", montant))
        position = 1

    elif position == 1 and prix >= prix_vente:
        print(">>> Vente de", montant, "XRP")
        print(place_order("sell", montant))
        position = 0

    time.sleep(3)
