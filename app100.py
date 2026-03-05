import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE TERMINAL BLOOMBERG (AVEC SCROLL POUR VOIR LES 100)
st.set_page_config(page_title="XRP 100 BOTS", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    .terminal-container {
        height: 800px;
        overflow-y: auto;
        border: 1px solid #222;
        padding: 10px;
        background-color: #000;
    }
    .bot-line {
        display: flex;
        justify-content: space-between;
        border-bottom: 1px solid #111;
        padding: 6px;
        color: white;
        font-family: 'Courier New', monospace;
        font-size: 13px;
    }
    .status-a { color: #FFA500; font-weight: bold; }
    .status-v { color: #00FF00; font-weight: bold; }
    .status-idle { color: #333; }
    .flash-box { background: #FFFF00; color: #000; padding: 0 6px; font-weight: bold; border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION ET MÉMOIRE
kraken = get_kraken_connection()

if 'bots_100' not in st.session_state:
    st.session_state.bots_100 = {f"B{i+1}": {"status": "IDLE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "oid": "NONE"} for i in range(100)}
    st.session_state.net_gain = 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ CMD CENTER")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    
    if st.button("🚨 INITIALISER 100 BOTS"):
        st.session_state.bots_100 = {f"B{i+1}": {"status": "IDLE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "oid": "NONE"} for i in range(100)}
        st.rerun()

    st.write("---")
    # Sélecteur pour ne pas surcharger la sidebar
    bot_sel = st.selectbox("CHOISIR BOT", [f"B{i+1}" for i in range(100)])
    if st.button(f"LANCER {bot_sel}"):
        if not kraken.markets: kraken.load_markets()
        pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
        pv_f = float(kraken.price_to_precision('XRP/USDC', p_out))
        vol = float(kraken.amount_to_precision('XRP/USDC', 25.0 / pa_f))
        try:
            res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
            st.session_state.bots_100[bot_sel].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "oid": res['id']})
            st.success(f"Ordre {bot_sel} envoyé !")
        except: st.error("Erreur Kraken")

# --- AFFICHAGE PRINCIPAL ---
st.title("🖥️ TERMINAL XRP - 100 BOTS")

try:
    px = kraken.fetch_ticker('XRP/USDC')['last']
    st.metric("XRP PRICE", f"{px:.4f} USDC", delta_color="normal")
except:
    px = 1.40
    st.warning("Connexion Kraken...")

# CONSTRUCTION DU TABLEAU HTML DES 100 BOTS
html_table = '<div class="terminal-container">'
for i in range(100):
    name = f"B{i+1}"
    bot = st.session_state.bots_100[name]
    st_class = "status-a" if bot["status"] == "ACHAT" else "status-v" if bot["status"] == "VENTE" else "status-idle"
    
    html_table += f'''
        <div class="bot-line">
            <span style="color:#555; width:40px;">{name}</span>
            <span class="{st_class}" style="width:80px;">{bot["status"]}</span>
            <span style="color:#888;">{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
            <span class="flash-box">25.00$</span>
        </div>
    '''
html_table += '</div>'

st.markdown(html_table, unsafe_allow_html=True)

time.sleep(10)
st.rerun()
