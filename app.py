import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE "BLOOMBERG HIGH-CONTRAST" (Fond Jaune, Chiffres Noirs)
st.set_page_config(page_title="XRP Bloomberg Contrast", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    
    /* CARTES EN JAUNE FLUO / CHIFFRES NOIRS */
    [data-testid="stMetric"] { 
        background-color: #FFFF00 !important; 
        border-radius: 5px; 
        padding: 10px;
    }
    [data-testid="stMetricValue"] { 
        color: #000000 !important; 
        font-size: 30px !important; 
        font-weight: 900 !important; 
    }
    [data-testid="stMetricLabel"] { 
        color: #333333 !important; 
        font-size: 12px !important; 
        font-weight: bold !important;
    }

    .bot-line {
        border-bottom: 1px solid #222222;
        padding: 8px 0px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 14px;
    }
    .p-in { color: #00FF00; font-weight: bold; }
    .p-out { color: #FF0000; font-weight: bold; }
    
    .flash-box {
        background-color: #FFFF00;
        color: #000000;
        padding: 2px 6px;
        border-radius: 2px;
        font-weight: 900;
        font-size: 13px;
    }
    .bot-id { color: #555555; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. MÉMOIRE ET CONFIG
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
    st.header("CMD")
    mode_reel = st.toggle("LIVE TRADING", value=True)
    p_in_set = st.number_input("TARGET IN", value=1.4440, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4460, format="%.4f")
    budget_base = st.number_input("BASE USD", value=10.0)
    st.divider()
    for i in range(10):
        name = f"Bot_{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"l_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    budget_actuel = budget_base + st.session_state.bots[name]["gain"]
                    qty = budget_actuel / p_in_set
                    pa, pv = float(kraken.price_to_precision('XRP/USDC', p_in_set)), float(kraken.price_to_precision('XRP/USDC', p_out_set))
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
        p_ask = float(ob['asks'][0][0]) if ob['asks'] else 0.0
        p_bid = float(ob['bids'][0][0]) if ob['bids'] else 0.0
        px = (p_ask + p_bid) / 2
        
        bal = kraken.fetch_balance()
        usdc = bal.get('free', {}).get('USDC', bal.get('free', {}).get('ZUSD', 0))

        with live.container():
            st.write(f"### MARKET FEED - XRP/USDC")
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{usdc:.2f}$")
            c2.metric("XRP PRICE", f"{px:.4f}")
            c3.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            
            st.divider()
            
            for i in range(10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                if bot["status"] != "LIBRE":
                    val_snow = budget_base + bot['gain']
                    status_color = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                    
                    st.markdown(f'''
                    <div class="bot-line">
                        <span class="bot-id">#{i+1:02d}</span>
                        <span style="color:{status_color}; font-weight:bold;">{bot["status"]}</span>
                        <span><span class="p-in">{bot["p_achat"]}</span> <small>→</small> <span class="p-out">{bot["p_vente"]}</span></span>
                        <span class="flash-box">{val_snow:.2f}$</span>
                        <span class="flash-box">{bot["cycles"]}</span>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # LOGIQUE TRADING
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
                            
                            new_budget = budget_base + st.session_state.bots[name]["gain"]
                            q = float(kraken.amount_to_precision('XRP/USDC', new_budget / bot['p_achat']))
                            res = kraken.create_order('XRP/USDC', 'limit', 'buy', q, bot['p_achat'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT"})
                            
                        sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                        st.rerun()

    except Exception as e:
        if "nonce" in str(e).lower(): time.sleep(1); continue
        st.write(f"SYSTEM: {str(e)[:20]}")
    time.sleep(20)
