import streamlit as st
import ccxt
import json
import os
from streamlit_autorefresh import st_autorefresh
from config import get_kraken_connection

# 1. CONFIGURATION & REFRESH AUTO (Toutes les 10s pour le prix, mais les clics sont instantanés)
st.set_page_config(page_title="XRP Turbo Terminal", layout="wide")
st_autorefresh(interval=10000, key="datarefresh")

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
    .badge-cash { background-color: #EAECEE; color: #566573; padding: 1px 6px; border-radius: 3px; font-size: 11px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION
kraken = get_kraken_connection()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
    st.session_state.profit_total = 0.0

# --- SIDEBAR (CLICS INSTANTANÉS) ---
with st.sidebar:
    st.header("⚡ TURBO CMD")
    p_in = st.number_input("IN", value=1.4000, format="%.4f")
    p_out = st.number_input("OUT", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET", value=25.0)
    
    bot_sel = st.selectbox("BOT", [f"B{i+1}" for i in range(100)])
    
    if st.button(f"🚀 LANCER {bot_sel}", use_container_width=True):
        try:
            if not kraken.markets: kraken.load_markets()
            pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
            vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
            res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
            st.session_state.bots[bot_sel].update({"status": "ACHAT", "pa": pa_f, "pv": p_out, "oid": res['id'], "budget": b_val})
            st.success(f"{bot_sel} LANCÉ !")
        except Exception as e: st.error(f"Erreur: {e}")

    if st.button("🚨 STOP TOUT", use_container_width=True):
        for b in st.session_state.bots:
            if st.session_state.bots[b]["oid"] != "NONE":
                try: kraken.cancel_order(st.session_state.bots[b]["oid"])
                except: pass
            st.session_state.bots[b].update({"status": "LIBRE", "oid": "NONE"})
        st.rerun()

# --- AFFICHAGE (SANS BOUCLE WHILE) ---
try:
    ticker = kraken.fetch_ticker('XRP/USDC')
    px = ticker['last']
    bal = kraken.fetch_balance()
    cash = bal.get('USDC', {}).get('free', 0.0)
    
    st.title("🖥️ TERMINAL XRP TURBO")
    c1, c2, c3 = st.columns(3)
    c1.metric("XRP PRICE", f"{px:.4f} $")
    c2.metric("GAIN TOTAL", f"+{st.session_state.profit_total:.4f} $")
    c3.metric("CASH DISPO", f"{cash:.2f} $")
    st.divider()

    actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
    for name in actifs:
        bot = st.session_state.bots[name]
        # Vérification rapide du statut de l'ordre
        try:
            order = kraken.fetch_order(bot["oid"])
            if order['status'] == 'closed' and bot["status"] == "ACHAT":
                st.session_state.bots[name]["status"] = "VENTE"
                # Ici on placerait l'ordre de vente réel...
        except: pass

        cl = "status-v" if bot["status"] == "VENTE" else "status-a"
        st.markdown(f'''
            <div class="bot-line">
                <b style="color:#2C3E50;">{name}</b>
                <span class="{cl}">{bot["status"]}</span>
                <span>{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
                <span class="badge-cash">CASH: {cash:.2f}$</span>
            </div>''', unsafe_allow_html=True)
except Exception as e:
    st.info("Connexion en cours...")
