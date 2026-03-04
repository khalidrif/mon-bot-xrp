import ccxt
import streamlit as st
import time

def get_kraken_connection():
    # Récupération sécurisée depuis le coffre-fort de Streamlit
    api_key = st.secrets.get("A2RXby/+ntL9pEZsOgfMeXSnGxYxntr59z+TxTcXJBlYDY+Ucz4M6f6N4", "").strip()
    api_secret = st.secrets.get("API_SEGPdLHKXJy2MQMzXn6KyjmqwYfkNHSTJvoCdV/oFuIntwCPbPVBC8QWYEBxPCAcvqLSfnx3/QqO+M6wD42Il0aA==", "").strip()

    if not api_key or not api_secret:
        # C'est ce message que vous voyez actuellement
        st.error("⚠️ CLÉS API MANQUANTES : Configurez les 'Secrets' dans Streamlit Cloud.")
        st.stop()

    exchange = ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'nonce': lambda: int(time.time() * 1000)}
    })
    
    # Correction définitive du "Markets not loaded"
    if not exchange.markets:
        exchange.load_markets()
        
    return exchange
