import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os
from config import get_kraken_connection

# --- 1. STYLE TERMINAL (STABLE ET FIXE) ---
st.set_page_config(page_title="XRP Terminal Live", layout="wide")
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #F0F2F6; overflow: hidden; }
    [data-testid="stMetric"] { background-color: #FFFF00 !important; border-radius: 8px; padding: 15px; border: 2px solid #000; min-height: 110px; }
    [data-testid="stMetricValue"] { color: #000 !important; font-size: 26px !important; font-weight: 900 !important; }
    .bot-line { background-color: #FFFFFF; border-radius: 5px; margin-bottom: 4px; padding: 10px; display: flex; justify-content: space-between; border: 1px solid #DDD; min-height: 48px; }
    [data-testid="stStatusWidget"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INIT & CONNEXION ---
SYMBOL = 'XRP/USDC'
FILE_MEMOIRE = "etat_bots.json"
kraken = get_kraken_connection()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
    st.session_state.profit_total = 0.0

# --- 3. LE FRAGMENT (RAFRAÎCHISSEMENT TOUTES LES 5 SECONDES) ---
@st.fragment(run_every=5)
def zone_live():
    try:
        # FORCE LE PRIX RÉEL : On ajoute un paramètre bidon pour bypasser le cache
        ticker = kraken.fetch_ticker(SYMBOL, params={'nonce': int(time.time() * 1000)})
        px = ticker['last']
        
        # Récupération balance (optionnel toutes les 5s)
        bal = kraken.fetch_balance()
        usdc = bal.get('total', {}).get('USDC', 0.0)

        # AFFICHAGE
        st.write(f"## 🏛️ TERMINAL TEMPS RÉEL - {SYMBOL}")
        k1, k2, k3 = st.columns(3)
        k1.metric("SOLDE USDC", f"{usdc:.2f} $")
        k2.metric("PRIX XRP", f"{px:.4f}") # <--- Ce prix va maintenant bouger !
        k3.metric("GAINS NETS", f"+{st.session_state.profit_total:.4f} $")
        st.divider()

        # Monitoring des Bots
        for i in range(10):
            name = f"Bot_{i+1}"
            bot = st.session_state.bots[name]
            if bot["status"] != "LIBRE" and bot["id"]:
                color = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                st.markdown(f'''
                <div class="bot-line">
                    <span style="font-weight:bold;">BOT {i+1:02d}</span>
                    <span style="color:{color}; font-weight:bold;">{bot["status"]}</span>
                    <span>{bot["p_achat"]} ➔ {bot["p_vente"]}</span>
                    <span style="background:#FFFF00; padding:2px 5px; font-weight:900; border:1px solid #000;">{10.0 + bot['gain']:.2f}$</span>
                </div>''', unsafe_allow_html=True)
                
                # Vérification auto sans recharger toute la page
                order = kraken.fetch_order(bot['id'], SYMBOL)
                if order['status'] == 'closed':
                    if bot["status"] == "ACHAT":
                        res = kraken.create_order(SYMBOL, 'limit', 'sell', order['filled'], bot['p_vente'])
                        st.session_state.bots[name].update({"id": res['id'], "status": "VENTE"})
                    else:
                        gain = (bot['p_vente'] - bot['p_achat']) * order['filled']
                        st.session_state.profit_total += gain
                        st.session_state.bots[name]["gain"] += gain
                        nq = float(kraken.amount_to_precision(SYMBOL, (10.0 + bot['gain']) / bot['p_achat']))
                        res = kraken.create_order(SYMBOL, 'limit', 'buy', nq, bot['p_achat'])
                        st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT"})
    except:
        st.caption("Sync...")

zone_live()
