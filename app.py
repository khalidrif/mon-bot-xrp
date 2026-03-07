import streamlit as st
import krakenex

st.title("TEST LIMIT ORDER KRAKEN – XRPUSDC")

api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRPUSDC"

# Récupérer le prix actuel
data = api.query_public("Ticker", {"pair": PAIR})
prix = float(data["result"][PAIR]["c"][0])

st.write("Prix actuel XRP :", prix)

# Prix LIMIT BUY placé au-dessus du marché => ordre visible
prix_limit = round(prix * 1.10, 6)
volume_xrp = 5  # minimum

st.write("Envoi d'un LIMIT BUY de 5 XRP à :", prix_limit)

order = {
    "pair": PAIR,
    "type": "buy",
    "ordertype": "limit",
    "price": prix_limit,
    "volume": volume_xrp,
    "oflags": "post"     # VERY IMPORTANT : l'ordre reste OUVERT
}

res = api.query_private("AddOrder", order)

st.subheader("Réponse Kraken :")
st.error(res)
