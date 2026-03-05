import ccxt
import time
import streamlit as st

def get_kraken_connection():
    try:
        # Récupération brute
        api_key = st.secrets["KRAKEN_KEY"].strip()
        api_secret = st.secrets["KRAKEN_SECRET"].strip()
        
        # DEBUG : Affiche la longueur des clés (pour vérifier si c'est coupé)
        # st.write(f"DEBUG: Longueur Key={len(api_key)}, Longueur Secret={len(api_secret)}")

        # Tentative de connexion directe
        return ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'nonce': lambda: str(int(time.time() * 1000))
            }
        })
    except Exception as e:
        st.error(f"ERREUR SECRETS : {str(e)}")
        return None
