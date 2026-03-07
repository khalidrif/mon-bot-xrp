import streamlit as st
import krakenex
import time

# ------------------------------------------
# CONFIGURATION API
# ------------------------------------------
api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRPUSDC"   # confirmé pour ton compte Québec

# Prix maximum = 5 décimales
def round_price(p):
    return float(f"{p:.5f}")

# Récupérer prix actuel
def get_price():
    d = api.query_public("Ticker", {"pair": PAIR})
    return float(d["result"][PAIR]["c"][0])

# Passer un LIMIT ORDER visible dans Kraken
def place_limit(order_type, price, volume):
    price = round_price(price)

    order = {
        "pair": PAIR,
        "type": order_type,
        "ordertype": "limit",
        "price": price,
        "volume": volume,
        "oflags": "post"  # reste visible dans Spot Orders
    }

    res = api.query_private("AddOrder", order)

    if res["error"]:
        st.error("Erreur Kraken : " + str(res["error"]))
    else:
        st.success(f"Ordre {order_type.upper()} envoyé !")

    return res

# ------------------------------------------
# INTERFACE
# ------------------------------------------
st.title("BOT SIMPLE – LIMIT BUY & LIMIT SELL (Kraken)")

prix_actuel = get_price()
st.info(f"Prix actuel XRP/USDC : {prix_actuel}")

prix_buy = st.number_input("Prix LIMIT BUY", value=round_price(prix_actuel - 0.05), format="%.5f")
prix_sell = st.number_input("Prix LIMIT SELL", value=round_price(prix_actuel + 0.05), format="%.5f")
montant_usdc = st.number_input("Montant USDC (min 5 XRP)", min_value=7.0)

if st.button("Envoyer LIMIT BUY"):
    montant_xrp = montant_usdc / prix_buy
    place_limit("buy", prix_buy, montant_xrp)
    st.write(f"BUY : {montant_xrp:.4f} XRP @ {prix_buy}")

if st.button("Envoyer LIMIT SELL"):
    montant_xrp = montant_usdc / prix_sell
    place_limit("sell", prix_sell, montant_xrp)
    st.write(f"SELL : {montant_xrp:.4f} XRP @ {prix_sell}")
