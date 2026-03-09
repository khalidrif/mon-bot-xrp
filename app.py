import streamlit as st
import ccxt
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Sniper", layout="wide")

@st.cache_resource
def get_exchange():
    # Utilisation d'un dictionnaire d'options pour stabiliser le Nonce
    ex = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {
            'nonce': 'milliseconds' # Utilise le temps précis pour éviter les doublons
        }
    })
    return ex

exchange = get_exchange()
symbol = "XRP/USDC"

# --- AJOUT D'UN TRY/EXCEPT SUR LE SOLDE ---
try:
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['last']
    
    # On entoure l'appel privé par un petit délai si nécessaire
    time.sleep(1) 
    bal = exchange.fetch_balance()
    
    usdc_bal = bal['free'].get('USDC', 0.0)
    xrp_bal = bal['free'].get('XRP', 0.0)
except ccxt.InvalidNonce:
    st.warning("⚠️ Problème de synchronisation (Nonce). Nouvel essai dans 5 secondes...")
    time.sleep(5)
    st.rerun()
except Exception as e:
    st.error(f"Erreur : {e}")
    st.stop()

# ... RESTE DU CODE (Colonnes, Boutons, etc.) ...
