import ccxt
import time
import streamlit as st

def get_kraken_connection():
    try:
        # Récupération sécurisée
        api_key = st.secrets["KRAKEN_KEY"].strip()
        api_secret = st.secrets["KRAKEN_SECRET"].strip()
        
        # Réparation forcée du padding (au cas où)
        api_secret = api_secret.replace('"', '').replace("'", "").replace(" ", "")
        while len(api_secret) % 4 != 0:
            api_secret += '='

        # Configuration de l'objet Kraken
        exchange = ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': 30000, # 30 secondes pour éviter les déconnexions
            'options': {
                'nonce': lambda: str(int(time.time() * 1000)),
                'fetchMinOrderAmounts': False  # Correction erreur "markets not loaded"
            }
        })
        
        return exchange

    except Exception as e:
        st.error(f"ERREUR CONFIGURATION : {e}")
        return None
