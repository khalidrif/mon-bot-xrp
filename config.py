
import ccxt
import streamlit as st

def get_kraken_connection():
    # Connexion sécurisée via les Secrets Streamlit
    exchange = ccxt.kraken({
        'apiKey': st.secrets["API_KEY"],
        'secret': st.secrets["API_SECRET"],
        'enableRateLimit': True,
        'timeout': 60000,
    })
    
    # FORCE LE CHARGEMENT (Règle ton erreur précédente)
    exchange.load_markets() 
    
    return exchange


