import streamlit as st
import pandas as pd
import ccxt
import time
import datetime
import json
import os
from config import get_kraken_connection

# 1. STYLE CRYSTAL
st.set_page_config(page_title="XRP Snowball Bot", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #050A0E; }
    [data-testid="stMetric"] { background-color: #0E161F; border: 1px solid #00FF88; padding: 15px; border-radius: 10px; }
    [data-testid="stMetricValue"] { color: #00FF88 !important; font-family: 'Segoe UI', sans-serif; font-size: 26px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. MÉMOIRE
FILE_MEMOIRE = "etat_bots.json"
def sauvegarder_donnees(bots, profit_total):
    with open(FILE_MEMOIRE, "w") as f: json.dump({"bots": bots, "profit_total": profit_total}, f)

def charger_donnees():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

# Initialisation
memoire = charger_donnees()
if 'bots' not in st.session_state:
    if memoire:
        st.session_state.bots = memoire["bots"]
        st.session_state.profit_total = memoire["profit_total"]
    else:
        st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
        st.session_state.profit_total = 0.0

kraken = get_kraken_connection()

# 3. SIDEBAR
with st.sidebar:
    st.header("💎 Snowball Pilot")
    mode_reel = st.toggle("💰 ARGENT RÉEL", value=False)
    p_achat_in = st.number_input("Prix Achat ($)", value=1.3560, format="%.4f")
    p_vente_in = st.number_input("Prix Vente ($)", value=1.3650, format="%.4f")
    budget_in = st.number_input("Budget Initial ($)", value=10.0)
    st.divider()
    for i in range(10):
        name = f"Bot_{i+1}"
        c_l, c_s = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c_l.button(f"LANCER {i+1}", key=f"l_{i}"):
                try:
                    kraken.load_markets()
                    qty = budget_in / p_achat_in
                    pa, pv = float(kraken.price_to_precision('XRP/USDC', p_achat_in)), float(kraken.price_to_precision('XRP/USDC', p_vente_in))
                    res = kraken.create_order('XRP/USDC', 'limit', 'buy', float(kraken.amount_to_precision('XRP/USDC', qty)), pa, {'validate': not mode_reel})
                    st.session_state.bots[name].update({"id": res['id'], "status": "ATTENTE_ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(e)
        else:
            if c_s.button(f"STOP {i+1}", key=f"stop_{i}"):
                try: kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# 4. ZONE LIVE
st.title("🛰️ Terminal : Valeur & Boule de Neige")
zone_live = st.empty()

while True:
    try:
        kraken.options['nonce'] = lambda: int(time.time() * 1000)
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        prix_reel = (float(ob['asks'][0][0]) + float(ob['bids'][0][0])) / 2
        balance = kraken.fetch_balance()
        usdc = balance.get('free', {}).get('USDC', balance.get('free', {}).get('ZUSD', 0))

        with zone_live.container():
            c1, c2, c3 = st.columns(3)
            c1.metric("SOLDE USDC", f"{usdc:,.2f} $")
            c2.metric("PRIX XRP", f"{prix_reel:.4f} $")
            c3.metric("TOTAL GAINS", f"+{st.session_state.profit_total:.4f} $")
            st.divider()
            
            # --- AFFICHAGE DES 10 ROBOTS ---
            r1 = st.columns(5)
            r2 = st.columns(5)
            all_cols = r1 + r2

            for i in range(10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                with all_cols[i]:
                    st.write(f"### 🤖 {i+1}")
                    
                    # LOGIQUE DE VALEUR ET ÉTAT
                    valeur_actuelle = budget_in + bot['gain']
                    
                    if bot["status"] == "ATTENTE_ACHAT":
                        st.warning(f"📥 @{bot['p_achat']}")
                        info = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        if info['status'] == 'closed':
                            res_v = kraken.create_order('XRP/USDC', 'limit', 'sell', info['filled'], bot['p_vente'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res_v['id'], "status": "ATTENTE_VENTE"})
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.rerun()
                    elif bot["status"] == "ATTENTE_VENTE":
                        st.success(f"📤 @{bot['p_vente']}")
                        valeur_actuelle = (budget_in + bot['gain']) / bot['p_achat'] * prix_reel
                        info_v = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        if info_v['status'] == 'closed':
                            gain = (bot['p_vente'] - bot['p_achat']) * info_v['filled']
                            st.session_state.profit_total += gain
                            st.session_state.bots[name]["gain"] += gain
                            st.session_state.bots[name]["cycles"] += 1
                            # BOULE DE NEIGE
                            nouveau_total = budget_in + st.session_state.bots[name]["gain"]
                            q = float(kraken.amount_to_precision('XRP/USDC', nouveau_total / bot['p_achat']))
                            res_n = kraken.create_order('XRP/USDC', 'limit', 'buy', q, bot['p_achat'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res_n['id'], "status": "ATTENTE_ACHAT"})
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.rerun()
                    else:
                        st.caption("Libre")
                        valeur_actuelle = 0.0

                    st.write(f"🔄 {bot['cycles']} | 💰 {bot['gain']:.4f}$")
                    st.metric("Valeur Live", f"{valeur_actuelle:.2f} $")

    except Exception as e: st.write(f"Flux... {e}")
    time.sleep(20)
