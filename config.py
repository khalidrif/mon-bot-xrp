import ccxt
import time
import streamlit as st

def get_kraken_connection():
    try:
        api_key = st.secrets["KRAKEN_KEY"].strip()
        api_secret = st.secrets["KRAKEN_SECRET"].strip()
        # Réparation padding
        api_secret = api_secret.replace('"', '').replace("'", "").replace(" ", "")
        while len(api_secret) % 4 != 0: api_secret += '='

        return ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'nonce': lambda: str(int(time.time() * 1000)),
                'nonceWindow': 5000,
                'fetchMinOrderAmounts': False 
            }
        })
    except Exception as e:
        st.error(f"Erreur Config: {e}")
        return None

