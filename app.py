import streamlit as st
import pandas as pd
import ccxt
import time
import datetime
import json
import os
from config import get_kraken_connection

# 1. STYLE "ELITE GLASS GOLD"
st.set_page_config(page_title="XRP Quantum Elite", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; }
    [data-testid="stMetric"] {
        background: rgba(255, 215, 0, 0.05);
        border: 1px solid rgba(255, 215, 0, 0.3);
        backdrop-filter: blur(10px);
        padding: 15px;
        border-radius: 12px;
    }
    .bot-header {
        color: #00FBFF; font-family: 'Segoe UI', sans-serif; font-size: 16px;
        font-weight: 800; text-shadow: 0px 0px 8px rgba(0, 251, 255, 0.6); margin-bottom: 8px;
    }
    .val-box {
        background: linear-gradient(90deg, #FFD700, #B8860B); color: #000000;
        padding: 3px 8px; border-radius: 4px; font-weight: 900; font-size: 13px; display: inline-block;
    }
    [data-testid="stMetricValue"] { color: #FFD700 !important; text-shadow: 0px 0px 10px rgba(255, 215, 0, 0.4); }
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

# Initialisation
memoire = charger_donnees()
if 'bots' not in st.session_state:
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
    st.session_state.profit_total = 0.0
    if memoire:
        st.session_state.bots.update(memoire["bots"])
        st.session_state.profit_total = memoire["profit_total"]

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛰️ Quantum Sidebar")
    mode_reel = st.toggle("💰 MODE RÉEL", value=True)
    p_in = st.number_input("Achat", value=1.4420, format="%.4f")
    p_out = st.number_input("Vente", value=1.4460, format="%.4f")
    budget = st.number_input("Budget", value=10.0)
    
    st.divider()
    for i in range(10):
        name = f"Bot_{i+1}"
        col1, col2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if col1.button(f"⚡ GO {i+1}", key=f"go_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    kraken.load_markets()
                    qty = (budget + st.session_state.bots[name]["gain"]) / p_in
                    pa = float(kraken.price_to_precision('XRP/USDC', p_in))
                    pv = float(kraken.price_to_precision('XRP/USDC', p_out))
                    res = kraken.create_order('XRP/USDC', 'limit', 'buy', float(kraken.amount_to_precision('XRP/USDC', qty)), pa, {'validate': not mode_reel})
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(e)
        else:
            if col2.button(f"🛑 OFF {i+1}", key=f"off_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# --- MAIN DASHBOARD ---
st.title("🌌 XRP QUANTUM TERMINAL")
live = st.empty()

while True:
    try:
        # --- CORRECTIF PRIX SÉCURISÉ ---
        kraken.options['nonce'] = lambda: int(time.time() * 1000)
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        
        # Extraction de l'élément [0][0] pour éviter l'erreur 'list'
        p_ask = float(ob['asks'][0][0]) if ob['asks'] else 0.0
        p_bid = float(ob['bids'][0][0]) if ob['bids'] else 0.0
        px = (p_ask + p_bid) / 2
        
        bal = kraken.fetch_balance()
        usdc = bal.get('free', {}).get('USDC', bal.get('free', {}).get('ZUSD', 0))

        with live.container():
            m1, m2, m3 = st.columns(3)
            m1.metric("BANKROLL", f"{usdc:,.2f} $")
            m2.metric("XRP PRICE", f"{px:.4f} $")
            m3.metric("TOTAL PROFIT", f"+{st.session_state.profit_total:.4f} $")
            
            st.divider()
            r1 = st.columns(5)
            r2 = st.columns(5)
            grid = r1 + r2

            for i in range(10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                with grid[i]:
                    st.markdown(f'<div class="bot-header">CORE {i+1}</div>', unsafe_allow_html=True)
                    v_live = budget + bot['gain']
                    
                    if bot["status"] == "ACHAT":
                        st.info(f"📥 BUY @{bot['p_achat']}")
                        info = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        if info['status'] == 'closed':
                            res_v = kraken.create_order('XRP/USDC', 'limit', 'sell', info['filled'], bot['p_vente'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res_v['id'], "status": "VENTE"})
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.rerun()
                    elif bot["status"] == "VENTE":
                        st.success(f"📤 SELL @{bot['p_vente']}")
                        v_live = (budget + bot['gain']) / bot['p_achat'] * px
                        info_v = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        if info_v['status'] == 'closed':
                            g = (bot['p_vente'] - bot['p_achat']) * info_v['filled']
                            st.session_state.profit_total += g
                            st.session_state.bots[name]["gain"] += g
                            st.session_state.bots[name]["cycles"] += 1
                            q = float(kraken.amount_to_precision('XRP/USDC', (budget + st.session_state.bots[name]["gain"]) / bot['p_achat']))
                            res_n = kraken.create_order('XRP/USDC', 'limit', 'buy', q, bot['p_achat'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res_n['id'], "status": "ACHAT"})
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.balloons()
                            st.rerun()
                    else: st.caption("STANDBY")

                    st.write(f"🔄 {bot['cycles']} | 💰 {bot['gain']:.4f}$")
                    st.markdown(f'<div class="val-box">VALUE: {v_live:.2f} $</div>', unsafe_allow_html=True)

    except Exception as e:
        if "nonce" in str(e).lower(): time.sleep(1); continue
        st.write(f"Sync... {e}")
    time.sleep(20)
