import ccxt
import time
import streamlit as st
import base64

def get_kraken_connection():
    try:
        # 1. Récupération et nettoyage extrême
        # On enlève TOUS les espaces, retours à la ligne et guillemets accidentels
        api_key = st.secrets["KRAKEN_KEY"].strip().replace('"', '').replace("'", "").replace(" ", "")
        api_secret = st.secrets["KRAKEN_SECRET"].strip().replace('"', '').replace("'", "").replace(" ", "")

        # 2. Correction forcée du padding Base64
        # Un secret Base64 doit avoir une longueur multiple de 4
        api_secret = api_secret.rstrip('=') # On enlève les '=' existants
        api_secret += '=' * (-len(api_secret) % 4) # On rajoute le compte exact de '='

        # 3. Test de validité interne avant d'envoyer à Kraken
        try:
            base64.b64decode(api_secret)
        except Exception:
            st.error("Le format du SECRET est corrompu. Recréez une clé sur Kraken.")
            return None

        # 4. Connexion CCXT
        return ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'nonce': lambda: str(int(time.time() * 1000))
            }
        })
    except Exception as e:
        st.error(f"Erreur configuration : {e}")
        return None
