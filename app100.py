import streamlit as st
import sys

# --- PATCH DE SÉCURITÉ CCXT / PYTHON 3.13 ---
try:
    import ccxt
except ImportError:
    st.error("Installation des composants en cours... Patientez 1 minute et faites REFRESH.")
    st.stop()

import time
import json
import os
from streamlit_autorefresh import st_autorefresh
from config import get_kraken_connection

# 1. STYLE CLAIR & TURBO
st.set_page_config(page_title="XRP Terminal 100", layout="wide")
st_autorefresh(interval=15000, key="datarefresh") # Refresh auto toutes les 15s

st.markdown("""
    <style>
    .stApp { background-color: #F0F2F6 !important; }
    .bot-line { 
        border-bottom: 1px solid #E6E9EF; padding: 8px 10px; display: flex; 
        justify-content: space-between; align-items: center; background-color: #FFF;
        margin-bottom: 2px; border-radius: 4px; font-size: 13px;
    }
    .status-v { color: #28a745; font-weight: bold; width: 60px; }
    .status-a { color: #fd7e14; font-weight: bold; width: 60px; }
    .badge-cash { background-color: #EAECEE; color: #566573; padding: 1px 6px; border-radius: 3px; font-size: 11px; border: 1px solid #D5D8DC; }
    .bot-id { color: #2C3E50; font-weight: bold; width: 40px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION KRAKEN
try:
    kraken = get_kraken_connection()
except Exception as e:
    st.sidebar.error(f"Clés API manquantes dans Secrets !")
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
    b_val = st.number_input("BUDGET (USDC)", value=25.0)
    
    bot_sel = st.selectbox("CHOISIR BOT", [f"B{i+1}" for i in range(100)])
    
    if st.button(f"🚀 GO {bot_sel}", use_container_width=True):
        if kraken:
            try:
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                st.session_state.bots[bot_sel].update({"status": "ACHAT", "pa": pa_f, "pv": p_out, "oid": res['id'], "budget": b_val})
                st.success(f"{bot_sel} Lancé !")
            except Exception as e: st.error(f"Kraken: {e}")

    if st.button("🚨 RESET ALL 100", use_container_width=True):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.rerun()

# --- AFFICHAGE PRINCIPAL ---
try:
    px = kraken.fetch_ticker('XRP/USDC')['last'] if kraken else 1.40
    bal = kraken.fetch_balance() if kraken else {}
    cash_dispo = bal.get('USDC', {}).get('free', 0.0)

    st.title("🖥️ TERMINAL XRP - 100 BOTS")
    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX XRP", f"{px:.4f} $")
    c2.metric("GAIN TOTAL", f"+{st.session_state.profit_total:.4f} $")
    c3.metric("CASH DISPO", f"{cash_dispo:.2f} $")
    st.divider()

    # AFFICHAGE DES 100 LIGNES (MÊME SI LIBRE)
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
                <span style="color:#888;">{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
                <span class="badge-cash">CASH: {cash_dispo:.2f}$</span>
                <span style="font-weight:bold;">{bot["budget"]:.2f}$</span>
            </div>''', unsafe_allow_html=True)
except Exception as e:
    st.warning("En attente de connexion Kraken...")

