import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE CLAIR ET PROFESSIONNEL (FINI LE NOIR)
st.set_page_config(page_title="XRP Terminal Clair", layout="wide")
st.markdown("""
    <style>
    /* Fond de page gris très léger */
    .stApp { background-color: #F0F2F6 !important; }
    
    /* Metrics en bleu sur blanc */
    [data-testid="stMetric"] { 
        background-color: #FFFFFF !important; 
        border: 1px solid #DDE1E7; 
        border-radius: 8px; 
        padding: 15px; 
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricValue"] { color: #0070FF !important; font-size: 24px !important; font-weight: 800 !important; }
    
    /* Lignes des bots propres */
    .bot-line { 
        border-bottom: 1px solid #E6E9EF; 
        padding: 10px 5px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #FFFFFF;
        margin-bottom: 2px;
    }
    .status-v { color: #28a745; font-weight: bold; } /* Vert */
    .status-a { color: #fd7e14; font-weight: bold; } /* Orange */
    .status-idle { color: #ABB2B9; }
    
    /* Badges de couleur */
    .flash-box { background-color: #FFC107; color: black; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .cycle-badge { background-color: #0070FF; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .bot-id { color: #2C3E50; font-weight: bold; width: 45px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION ET MÉMOIRE
kraken = get_kraken_connection()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
    st.session_state.profit_total = 0.0

# --- RÉGLAGES À GAUCHE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ CONFIGURATION")
    p_in = st.number_input("PRIX ACHAT (IN)", value=1.4000, format="%.4f")
    p_out = st.number_input("PRIX VENTE (OUT)", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET (USDC)", value=25.0)
    
    if st.button("🚨 RÉINITIALISER TOUT"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.rerun()
    
    st.divider()
    bot_sel = st.selectbox("SÉLECTIONNER BOT", [f"B{i+1}" for i in range(100)])
    
    c1, c2 = st.columns(2)
    if c1.button(f"🚀 GO {bot_sel}"):
        if kraken:
            try:
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                pv_f = float(kraken.price_to_precision('XRP/USDC', p_out))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                st.session_state.bots[bot_sel].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "oid": res['id']})
                st.rerun()
            except Exception as e: st.error(f"Erreur Kraken")
    
    if c2.button(f"🛑 STOP"):
        st.session_state.bots[bot_sel].update({"status": "LIBRE", "oid": "NONE"})
        st.rerun()

# --- AFFICHAGE À DROITE (PRINCIPAL) ---
live = st.empty()
count = 0
while True:
    try:
        if kraken:
            px = kraken.fetch_ticker('XRP/USDC')['last']
        else:
            px = 0.0
            
        with live.container():
            st.title("🖥️ TERMINAL XRP - 100 BOTS")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("PRIX XRP", f"{px:.4f}")
            col2.metric("GAIN TOTAL", f"+{st.session_state.profit_total:.4f}")
            col3.metric("BOTS ACTIFS", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            st.divider()
            
            # Affichage des 100 lignes
            for i in range(100):
                name = f"B{i+1}"
                bot = st.session_state.bots[name]
                st_lab = bot["status"]
                
                # Classes CSS
                sc_class = "status-v" if st_lab == "VENTE" else "status-a" if st_lab == "ACHAT" else "status-idle"
                label_txt = st_lab if st_lab != "LIBRE" else "IDLE"
                
                st.markdown(f'''
                    <div class="bot-line">
                        <span class="bot-id">{name}</span>
                        <span class="{sc_class}">{label_txt}</span>
                        <span style="color:#566573;">{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
                        <span class="cycle-badge">{bot.get("cycles", 0)} CYCLES</span>
                        <span class="flash-box">{bot["budget"] + bot["gain"]:.2f} $</span>
                    </div>''', unsafe_allow_html=True)
    except: pass
    count += 1
    time.sleep(10)
