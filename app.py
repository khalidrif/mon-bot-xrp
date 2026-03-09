import streamlit as st
import ccxt
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Snowball Bot", layout="wide")
st.title("🤖 Bot XRP/USDC - Kraken")

# Récupération des Secrets GitHub/Streamlit
API_KEY = os.getenv('KRAKEN_API_KEY')
API_SECRET = os.getenv('KRAKEN_API_SECRET')

if not API_KEY:
    st.error("Clés API manquantes. Configurez les 'Secrets' dans Streamlit.")
    st.stop()

# Connexion Kraken
exchange = ccxt.kraken({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

# --- FONCTION DE CALCUL RSI (SANS PANDAS_TA) ---
def calculate_rsi(prices, period=14):
    if len(prices) < period: return 50
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 = rs))

# --- INTERFACE ET LOGIQUE ---
st.write("Surveillance du marché en cours...")

try:
    ticker = exchange.fetch_ticker('XRP/USDC')
    price = ticker['last']
    st.metric("Prix XRP/USDC", f"{price} USDC")
    
    # Simulation d'achat/vente simplifiée
    if st.button("Lancer un cycle manuel"):
        st.info(f"Tentative d'achat au prix de {price}...")
        # L'ordre réel se placerait ici
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
