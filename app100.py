import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE BLOOMBERG ORIGINAL
st.set_page_config(page_title="XRP 100 BOTS TERMINAL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    [data-testid="stMetric"] { background-color: #FFFFFF !important; border-radius: 4px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 20px !important; font-weight: 900 !important; }
    .bot-line { border-bottom: 1px solid #222222; padding: 6px 0px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: white; }
    .status-v { color: #00FF00; font-weight: bold; }
    .status-a { color: #FFA500; font-weight: bold; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 1px 6px; border-radius: 2px; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION ET MÉMOIRE
kraken = get_kraken_connection()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
    st.session_state.profit_total = 0.0

# --- REGLAGE GAUCHE (SIDEBAR) ---
with st.sidebar:
    st.header("⚡ CMD CENTER")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET (USDC)", value=25.0)
    
    # Bouton Reset dans la barre de gauche
    if st.button("🚨 RESET ALL 100 BOTS"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.rerun()
    
    st.divider()
    # Sélecteur de bot pour ne pas avoir une sidebar de 2km
    bot_sel = st.selectbox("CHOISIR BOT", [f"B{i+1}" for i in range(100)])
    if st.button(f"🚀 LANCER {bot_sel}"):
        if not kraken.markets: kraken.load_markets()
        pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
        pv_f = float(kraken.price_to_precision('XRP/USDC', p_out))
        vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
        try:
            res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
            st.session_state.bots[bot_sel].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "oid": res['id']})
            st.rerun()
        except: st.error("Erreur Kraken")

# --- AFFICHAGE DROITE (PRINCIPAL) ---
live = st.empty()
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        with live.container():
            st.write(f"### MARKET FEED : {px:.4f} XRP/USDC")
            col1, col2 = st.columns(2)
            col1.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            col2.metric("BOTS ON", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            st.divider()
            
            # Affichage des 100 lignes
            for i in range(100):
                name = f"B{i+1}"
                bot = st.session_state.bots[name]
                st_lab = bot["status"]
                sc = "status-v" if st_lab == "VENTE" else "status-a" if st_lab == "ACHAT" else ""
                
                st.markdown(f'''
                    <div class="bot-line">
                        <span style="color:#555;">{name}</span>
                        <span class="{sc}">{st_lab if st_lab != "LIBRE" else "IDLE"}</span>
                        <span>{bot["pa"]} → {bot["pv"]}</span>
                        <span class="flash-box">{bot.get("cycles", 0)} CYC</span>
                        <span class="flash-box">{bot["budget"] + bot["gain"]:.2f} $</span>
                    </div>''', unsafe_allow_html=True)
    except: pass
    time.sleep(10)
