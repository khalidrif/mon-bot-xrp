import streamlit as st
import krakenex

st.title("TEST ORDRE KRAKEN")

api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

st.write("Envoi d’un ordre TEST BUY 5 XRP sur XRPUSDC…")

res = api.query_private("AddOrder", {
    "pair": "XRPUSDC",
    "type": "buy",
    "ordertype": "market",
    "volume": 5
})

st.error(res)
