import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE NANO TEXT (Sobre et efficace)
st.set_page_config(page_title="XRP Nano Fix", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetric"] { background-color: #1A1C23; border: 1px solid #30363D; border-radius: 4px; padding: 5px; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 18px !important; }
    .nano-text { font-size: 11px; color: #8B949E; margin: 0; }
    .status-buy { color: #FFA500; font-weight: bold; font-size: 11px; }
    .status-sell { color: #00FF88; font-weight: bold; font-size: 11px; }
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

kraken = get_kraken_connection()
memoire = charger_donnees()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
    st.session_state.profit_total = 0.0
    if memoire:
        st.session_state.bots.update(memoire["bots"])
        st.session_state.profit_total = memoire.get("profit_total", 0.0)

# --- SIDEBAR ---
with st.sidebar:
    st.caption("Contrôle")
    mode_reel = st.toggle("Réel", value=True)
    p_in = st.number_input("In", value=1.1200, format="%.4f")
    p_out = st.number_input("Out", value=1.4400, format="%.4f")
    budget = st.number_input("$", value=10.0)
    st.divider()
    for i in range(10):
        name = f"Bot_{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c1.button(f"ON {i+1}", key=f"go_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    qty = (budget + st.session_state.bots[name]["gain"]) / p_in
                    pa, pv = float(kraken.price_to_precision('XRP/USDC', p_in)), float(kraken.price_to_precision('XRP/USDC', p_out))
                    res = kraken.create_order('XRP/USDC', 'limit', 'buy', float(kraken.amount_to_precision('XRP/USDC', qty)), pa, {'validate': not mode_reel})
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(e)
        else:
            if c2.button(f"OFF {i+1}", key=f"off_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# --- MAIN ---
live = st.empty()

while True:
    try:
        kraken.options['nonce'] = lambda: int(time.time() * 1000)
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        
        # --- FIX DÉFINITIF DU PRIX ---
        p_ask = float(ob['asks'][0][0]) if ob['asks'] else 0.0
        p_bid = float(ob['bids'][0][0]) if ob['bids'] else 0.0
        px = (p_ask + p_bid) / 2
        
        bal = kraken.fetch_balance()
        usdc = bal.get('free', {}).get('USDC', bal.get('free', {}).get('ZUSD', 0))

        with live.container():
            m1, m2, m3 = st.columns(3)
            m1.metric("CASH", f"{usdc:.2f}$")
            m2.metric("XRP", f"{px:.4f}")
            m3.metric("GAIN", f"+{st.session_state.profit_total:.4f}")
            
            grid = st.columns(5)
            grid2 = st.columns(5)
            all_c = grid + grid2

            for i in range(10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                with all_c[i]:
                    st.markdown(f"**{i+1}**")
                    if bot["status"] != "LIBRE":
                        color_class = "status-buy" if bot["status"] == "ACHAT" else "status-sell"
                        st.markdown(f'<span class="{color_class}">{bot["status"]}</span>', unsafe_allow_html=True)
                        st.markdown(f'<p class="nano-text">In: {bot["p_achat"]}<br>Out: {bot["p_vente"]}</p>', unsafe_allow_html=True)
                        
                        info = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        if info['status'] == 'closed':
                            if bot["status"] == "ACHAT":
                                res = kraken.create_order('XRP/USDC', 'limit', 'sell', info['filled'], bot['p_vente'], {'validate': not mode_reel})
                                st.session_state.bots[name].update({"id": res['id'], "status": "VENTE"})
                            else:
                                g = (bot['p_vente'] - bot['p_achat']) * info['filled']
                                st.session_state.profit_total += g
                                st.session_state.bots[name]["gain"] += g
                                st.session_state.bots[name]["cycles"] += 1
                                q = float(kraken.amount_to_precision('XRP/USDC', (budget + st.session_state.bots[name]["gain"]) / bot['p_achat']))
                                res = kraken.create_order('XRP/USDC', 'limit', 'buy', q, bot['p_achat'], {'validate': not mode_reel})
                                st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT"})
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.rerun()
                    else:
                        st.markdown('<p class="nano-text">---</p>', unsafe_allow_html=True)
                    st.caption(f"C:{bot['cycles']} | +{bot['gain']:.2f}")

    except Exception as e:
        if "nonce" in str(e).lower(): time.sleep(1); continue
        st.error(f"Erreur : {str(e)[:30]}")
    time.sleep(20)
