import streamlit as st
import time
import json
import os

# 1. CONFIGURATION ET STYLE (DOIT ÊTRE EN HAUT)
st.set_page_config(page_title="XRP 100 BOTS", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    .main-title { color: #FFFF00; font-family: 'Courier New', monospace; text-align: center; border-bottom: 2px solid #222; padding: 10px; }
    .bot-line { 
        border-bottom: 1px solid #111; 
        padding: 6px; 
        display: flex; 
        justify-content: space-between; 
        color: #FFFFFF;
        font-family: 'Courier New', monospace;
        font-size: 13px;
    }
    .flash-box { background-color: #FFFF00; color: #000; padding: 0 6px; font-weight: bold; border-radius: 2px; }
    .status-idle { color: #444; }
    .status-on { color: #00FF00; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. INITIALISATION MÉMOIRE SANS KRAKEN
if 'bots' not in st.session_state:
    # ON FORCE LA CRÉATION DES 100 BOTS EN MÉMOIRE
    st.session_state.bots = {f"B{i+1}": {"status": "IDLE", "pa": 0.0, "pv": 0.0, "budget": 25.0} for i in range(100)}
    st.session_state.net_gain = 0.0

# --- INTERFACE VISIBLE ---
st.markdown('<div class="main-title"><h1>XRP BLOOMBERG TERMINAL - 100 BOTS</h1></div>', unsafe_allow_html=True)

# SIDEBAR DE CONTRÔLE
with st.sidebar:
    st.header("⚡ CMD CENTER")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    if st.button("🚨 RESET FORCE 100"):
        st.session_state.bots = {f"B{i+1}": {"status": "IDLE", "pa": 0.0, "pv": 0.0, "budget": 25.0} for i in range(100)}
        st.rerun()

# 3. AFFICHAGE DES 100 LIGNES (SÉCURISÉ)
# On utilise un conteneur pour les metrics
c1, c2 = st.columns(2)
c1.metric("BANKROLL DISPO", "Chargement...")
c2.metric("NET GAIN TOTAL", f"+{st.session_state.net_gain:.4f}")

st.write("---")

# BOUCLE D'AFFICHAGE DES 100 LIGNES
for i in range(100):
    name = f"B{i+1}"
    bot = st.session_state.bots[name]
    
    st.markdown(f'''
        <div class="bot-line">
            <span style="color:#666; width:50px;">{name}</span>
            <span class="status-idle">{bot["status"]}</span>
            <span style="color:#333;">{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
            <span class="flash-box">{bot["budget"]:.2f} $</span>
        </div>
    ''', unsafe_allow_html=True)

# 4. CHARGEMENT DE KRAKEN (APRÈS L'AFFICHAGE)
try:
    from config import get_kraken_connection
    import ccxt
    kraken = get_kraken_connection()
    if kraken:
        ticker = kraken.fetch_ticker('XRP/USDC')
        st.sidebar.success(f"✅ LIVE: {ticker['last']}")
except Exception as e:
    st.sidebar.error(f"Connexion Kraken en attente...")
