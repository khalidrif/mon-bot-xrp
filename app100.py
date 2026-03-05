import streamlit as st
import sys

# --- PATCH DE SÉCURITÉ ---
try:
    import ccxt
except ImportError:
    st.error("Installation en cours... Patientez 1 minute.")
    st.stop()

import time
import json
import os
from streamlit_autorefresh import st_autorefresh
from config import get_kraken_connection

# 1. RETOUR AU STYLE "BLOOMBERG ORIGINAL"
st.set_page_config(page_title="XRP Bloomberg 100", layout="wide")
st_autorefresh(interval=15000, key="datarefresh") # Refresh auto 15s

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    [data-testid="stMetric"] { background-color: #FFFFFF !important; border-radius: 4px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 20px !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 12px !important; font-weight: bold !important; }
    .bot-line { 
        border-bottom: 1px solid #222222; padding: 8px 0px; display: flex; 
        justify-content: space-between; align-items: center; font-size: 13px; color: white;
        font-family: 'Courier New', monospace;
    }
    .status-v { color: #00FF00; font-weight: bold; }
    .status-a { color: #FFA500; font-weight: bold; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 2px 6px; border-radius: 2px; font-weight: 900; }
    .badge-cash { background-color: #222222; color: #888; padding: 2px 6px; border-radius: 2px; font-size: 11px; }
    .bot-id { color: #555555; font-weight: bold; width: 40px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION KRAKEN
try:
    kraken = get_kraken_connection()
except:
    kraken = None

# 3. MÉMOIRE DES 100 BOTS
if 'bots' not in st.session_state:
    st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
    st.session_state.profit_total = 0.0

# --- SIDEBAR CMD ---
with st.sidebar:
    st.header("⚡ CMD 100 BOTS")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET", value=25.0)
    
    bot_sel = st.selectbox("SÉLECTION BOT", [f"B{i+1}" for i in range(100)])
    
    if st.button(f"🚀 GO {bot_sel}", use_container_width=True):
        if kraken:
            try:
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                st.session_state.bots[bot_sel].update({"status": "ACHAT", "pa": pa_f, "pv": p_out, "oid": res['id'], "budget": b_val})
                st.success(f"Ordre {bot_sel} envoyé !")
            except Exception as e: st.error(f"Kraken: {e}")

    if st.button("🚨 RESET ALL 100", use_container_width=True):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.rerun()

# --- MAIN DISPLAY ---
try:
    px = kraken.fetch_ticker('XRP/USDC')['last'] if kraken else 1.40
    bal = kraken.fetch_balance() if kraken else {}
    cash = bal.get('USDC', {}).get('free', 0.0)

    st.write(f"### MARKET FEED : {px:.4f} XRP/USDC")
    c1, c2, c3 = st.columns(3)
    c1.metric("BANKROLL", f"{cash:.2f} $")
    c2.metric("NET GAIN", f"+{st.session_state.profit_total:.4f} $")
    c3.metric("BOTS ACTIFS", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
    st.divider()

    # AFFICHAGE DES 100 LIGNES
    for i in range(100):
        name = f"B{i+1}"
        bot = st.session_state.bots[name]
        st_lab = bot["status"]
        cl = "status-v" if st_lab == "VENTE" else "status-a" if st_lab == "ACHAT" else "status-idle"
        txt_status = st_lab if st_lab != "LIBRE" else "IDLE"
        
        st.markdown(f'''
            <div class="bot-line">
                <span class="bot-id">{name}</span>
                <span class="{cl}">{txt_status}</span>
                <span style="color:#555;">{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
                <span class="badge-cash">CASH: {cash:.2f}$</span>
                <span class="flash-box">{bot["budget"] + bot["gain"]:.2f} $</span>
            </div>''', unsafe_allow_html=True)
except:
    st.info("Chargement du Terminal Bloomberg...")
