import ccxt
import time
import streamlit as st

def get_kraken_connection():
    # Récupération sécurisée via Streamlit Secrets
    try:
        api_key = st.secrets["KRAKEN_KEY"].strip()
        api_secret = st.secrets["KRAKEN_SECRET"].strip()
    except Exception as e:
        st.error("ERREUR SECRETS : Vérifiez KRAKEN_KEY et KRAKEN_SECRET dans Streamlit Settings.")
        return None

    return ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            # Correction définitive de l'erreur "Invalid Nonce"
            'nonce': lambda: str(int(time.time() * 1000))
        }
    })
