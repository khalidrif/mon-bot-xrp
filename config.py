import ccxt
import streamlit as st

def get_kraken_connection():
    # On utilise les étiquettes, PAS tes vrais codes ici
    api_key = st.secrets["API_KEY"]
    api_secret = st.secrets["API_SECRET"]

    return ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })
