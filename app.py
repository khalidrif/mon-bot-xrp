import streamlit as st
import time
import krakenex

api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRPUSDC"   # validé pour ton compte

# --- Fonction pour obtenir le prix actuel ---
def get_price():
    data = api.query_public("Ticker", {"pair": PAIR})
    return float(data["result"][PAIR]["c"][0])

st.title("AFFICHAGE PRIX XRPUSDC + TEST LIMIT ORDER")

# afficher prix en temps réel
price_placeholder = st.empty()

while True:
    prix = get_price()
    price_placeholder.info("Prix actuel XRP/USDC : " + str(prix))

    time.sleep(2)
