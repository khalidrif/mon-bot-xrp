import ccxt
import time
import streamlit as st

def get_kraken_connection():
    try:
        # Récupération sécurisée
        api_key = st.secrets["KRAKEN_KEY"].strip()
        api_secret = st.secrets["KRAKEN_SECRET"].strip()
        
        # Réparation forcée du padding Base64
        api_secret = api_secret.replace('"', '').replace("'", "").replace(" ", "")
        while len(api_secret) % 4 != 0:
            api_secret += '='

        return ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': 30000,
            'options': {
                'nonce': lambda: str(int(time.time() * 1000)),
                'nonceWindow': 5000,  # Évite les erreurs "Invalid Nonce"
                'fetchMinOrderAmounts': False 
            }
        })
    except Exception as e:
        st.error(f"ERREUR CONFIG : {e}")
        return None
