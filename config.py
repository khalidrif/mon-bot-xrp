import ccxt
import time
import streamlit as st
import base64

def get_kraken_connection():
    try:
        # 1. Récupération brute
        api_key = st.secrets["KRAKEN_KEY"].strip()
        api_secret = st.secrets["KRAKEN_SECRET"].strip()
        
        # 2. NETTOYAGE RADICAL (Supprime espaces, guillemets et sauts de ligne)
        api_secret = api_secret.replace('"', '').replace("'", "").replace(" ", "").replace("\n", "")
        
        # 3. RÉPARATION FORCÉE DU PADDING
        # On ajoute des '=' jusqu'à ce que la longueur soit un multiple de 4
        while len(api_secret) % 4 != 0:
            api_secret += '='

        # 4. TEST DE DÉCODAGE LOCAL
        base64.b64decode(api_secret)

        return ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'nonce': lambda: str(int(time.time() * 1000))
            }
        })
    except Exception as e:
        st.error(f"ERREUR PADDING RÉPARÉE MAIS INVALIDE : {e}")
        return None

