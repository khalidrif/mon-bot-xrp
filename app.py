import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE NANO TEXT (Zéro barre, juste les chiffres)
st.set_page_config(page_title="XRP Nano Text", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetric"] { background-color: #1A1C23; border: 1px solid #30363D; border-radius: 4px; padding: 5px; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 18px !important; }
    
    .nano-text { font-size: 11px; color: #8B949E; margin: 0; }
    .status-buy { color: #FFA500; font-weight: bold; font-size: 11px; }
    .status-sell { color: #00FF88; font-weight: bold; font-size: 11px; }
    .target-price { color: #FFFFFF; font-family: monospace; }
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
        st.session_state.profit_total = memoire["profit_total"]

# --- SIDEBAR COMPACTE ---
with st.sidebar:
    st.caption("Réglages")
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
        p_ask = float(ob['asks'])
        p_bid = float(ob['bids'])
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
                    st.markdown(f"**Bot {i+1}**")
                    if bot["status"] != "LIBRE":
                        # Affichage textuel simple des cibles
                        if bot["status"] == "ACHAT":
                            st.markdown(f'<span class="status-buy">ACHAT</span> @<span class="target-price">{bot["p_achat"]}</span>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<span class="status-sell">VENTE</span> @<span class="target-price">{bot["p_vente"]}</span>', unsafe_allow_html=True)
                        
                        st.markdown(f'<p class="nano-text">Cible Out: {bot["p_vente"]}</p>', unsafe_allow_html=True)
                        
                        # LOGIQUE ACHAT/VENTE
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
                    
                    st.markdown(f'<p class="nano-text">Cyc:{bot["cycles"]} | +{bot["gain"]:.3f}$</p>', unsafe_allow_html=True)

    except Exception as e:
        if "nonce" in str(e).lower(): time.sleep(1); continue
        st.caption(f"ERR: {str(e)[:20]}")
    time.sleep(20)
