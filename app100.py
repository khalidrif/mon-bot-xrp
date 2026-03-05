import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE CLAIR ET PROPRE (PAS NOIR)
st.set_page_config(page_title="XRP 100 BOTS", layout="wide")
st.markdown("""
    <style>
    .bot-row { 
        border-bottom: 1px solid #ddd; 
        padding: 10px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        font-family: monospace; 
        background-color: white;
    }
    .status-a { color: orange; font-weight: bold; }
    .status-v { color: green; font-weight: bold; }
    .status-idle { color: #aaa; }
    .badge-cash { background-color: #FFD700; color: black; padding: 2px 8px; font-weight: bold; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION KRAKEN
kraken = get_kraken_connection()

# 3. MÉMOIRE DES 100 BOTS
if 'bots_100' not in st.session_state:
    st.session_state.bots_100 = {f"B{i+1}": {"status": "IDLE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "oid": "NONE"} for i in range(100)}
    st.session_state.gain_total = 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ CONFIGURATION")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    
    if st.button("🚨 INITIALISER 100 BOTS"):
        st.session_state.bots_100 = {f"B{i+1}": {"status": "IDLE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "oid": "NONE"} for i in range(100)}
        st.rerun()

    st.write("---")
    # Liste de contrôle pour activer les bots
    for i in range(100):
        name = f"B{i+1}"
        if st.session_state.bots_100[name]["status"] == "IDLE":
            if st.button(f"LANCER {name}", key=f"run_{i}"):
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                pv_f = float(kraken.price_to_precision('XRP/USDC', p_out))
                vol = float(kraken.amount_to_precision('XRP/USDC', 25.0 / pa_f))
                try:
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                    st.session_state.bots_100[name].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "oid": res['id']})
                    st.rerun()
                except: st.error("Erreur Kraken")

# --- INTERFACE PRINCIPALE ---
st.title("🖥️ TERMINAL XRP - 100 BOTS")

try:
    px = kraken.fetch_ticker('XRP/USDC')['last']
    st.metric("PRIX XRP LIVE", f"{px:.4f} USDC")
except:
    st.warning("Connexion Kraken en attente...")
    px = 1.40

st.write(f"**NET GAIN : +{st.session_state.gain_total:.4f}**")
st.divider()

# --- AFFICHAGE STRICT DES 100 LIGNES ---
for i in range(100):
    name = f"B{i+1}"
    bot = st.session_state.bots_100[name]
    
    # Détermination du style
    if bot["status"] == "ACHAT":
        st_class = "status-a"
        label = "ACHAT"
    elif bot["status"] == "VENTE":
        st_class = "status-v"
        label = "VENTE"
    else:
        st_class = "status-idle"
        label = "IDLE"

    # Ligne de bot
    st.markdown(f'''
        <div class="bot-row">
            <span style="font-weight:bold; width:60px;">{name}</span>
            <span class="{st_class}" style="width:80px;">{label}</span>
            <span>{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
            <span class="badge-cash">25.00 $</span>
        </div>
    ''', unsafe_allow_html=True)

# Rafraîchissement automatique
time.sleep(10)
st.rerun()
