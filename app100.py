import streamlit as st
import sys

# --- PATCH DE SÉCURITÉ CCXT ---
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

# 1. STYLE CLAIR & INDICATEUR LIVE
st.set_page_config(page_title="XRP Terminal Pro", layout="wide")
st_autorefresh(interval=15000, key="datarefresh") 

st.markdown("""
    <style>
    .stApp { background-color: #F0F2F6 !important; }
    
    .status-dot {
        height: 10px; width: 10px; background-color: #00FF00;
        border-radius: 50%; display: inline-block;
        box-shadow: 0 0 8px #00FF00;
        animation: blinker 1.5s linear infinite;
        margin-right: 10px;
    }
    @keyframes blinker { 50% { opacity: 0; } }

    [data-testid="stMetric"] { background-color: #FFFFFF !important; border: 1px solid #DDE1E7; border-radius: 8px; padding: 15px; }
    [data-testid="stMetricValue"] { color: #0070FF !important; font-size: 24px !important; font-weight: 800 !important; }
    
    .bot-line { 
        border-bottom: 1px solid #E6E9EF; padding: 12px 10px; display: flex; 
        justify-content: space-between; align-items: center; background-color: #FFFFFF;
        margin-bottom: 3px; border-radius: 5px; font-size: 13px;
    }
    .status-v { color: #28a745; font-weight: bold; width: 60px; }
    .status-a { color: #fd7e14; font-weight: bold; width: 60px; }
    .flash-box { background-color: #FFC107; color: black; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    
    /* STYLE POUR LES CYCLES SUR LA LIGNE */
    .badge-cycle { background-color: #EAECEE; color: #1B2631; padding: 1px 10px; border-radius: 3px; font-size: 11px; font-weight: 900; border: 1px solid #D5D8DC; }
    
    .bot-id { color: #2C3E50; font-weight: bold; width: 50px; }
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
    st.header("⚙️ CONFIGURATION")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET (USDC)", value=25.0)
    
    st.divider()
    bot_sel = st.selectbox("SÉLECTIONNER BOT", [f"B{i+1}" for i in range(100)])
    
    if st.button(f"🚀 GO {bot_sel}", use_container_width=True):
        if kraken:
            try:
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                st.session_state.bots[bot_sel].update({"status": "ACHAT", "pa": pa_f, "pv": p_out, "oid": res['id'], "budget": b_val})
                st.rerun()
            except Exception as e: st.error(f"Kraken: {e}")

    if st.button("🚨 STOP TOUS LES BOTS", use_container_width=True):
        for b in st.session_state.bots:
            st.session_state.bots[b].update({"status": "LIBRE", "oid": "NONE"})
        st.rerun()

# --- MAIN DISPLAY ---
try:
    px = kraken.fetch_ticker('XRP/USDC')['last'] if kraken else 0.0
    bal = kraken.fetch_balance() if kraken else {}
    cash = bal.get('USDC', {}).get('free', 0.0)

    st.markdown(f'<h3><span class="status-dot"></span>TERMINAL XRP LIVE</h3>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX XRP", f"{px:.4f} $")
    c2.metric("GAIN TOTAL", f"+{st.session_state.profit_total:.4f} $")
    c3.metric("CASH DISPO", f"{cash:.2f} $")
    st.divider()

    actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]

    if not actifs:
        st.info("Aucun bot actif. Utilisez la barre latérale pour démarrer.")
    else:
        for name in actifs:
            bot = st.session_state.bots[name]
            st_lab = bot["status"]
            cl = "status-v" if st_lab == "VENTE" else "status-a"
            
            st.markdown(f'''
                <div class="bot-line">
                    <span class="bot-id">{name}</span>
                    <span class="{cl}">{st_lab}</span>
                    <span>{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
                    <span class="badge-cycle">{bot.get("cycles", 0)} CYCLES</span>
                    <span class="flash-box">{bot["budget"] + bot["gain"]:.2f} $</span>
                </div>''', unsafe_allow_html=True)
except:
    st.info("Connexion Kraken en cours...")
