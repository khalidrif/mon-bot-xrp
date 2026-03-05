import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE "BLOOMBERG HIGH-CONTRAST"
st.set_page_config(page_title="XRP Bloomberg FORCE LIVE", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    [data-testid="stMetric"] { background-color: #FFFFFF !important; border-radius: 4px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 20px !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 12px !important; font-weight: bold !important; }
    .bot-line { border-bottom: 1px solid #222222; padding: 8px 0px; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
    .p-in { color: #00FF00; font-weight: bold; }
    .p-out { color: #FF0000; font-weight: bold; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 2px 6px; border-radius: 2px; font-weight: 900; font-size: 13px; }
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
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(100)}
    st.session_state.profit_total = 0.0
    if memoire:
        st.session_state.bots.update(memoire.get("bots", {}))
        st.session_state.profit_total = memoire.get("profit_total", 0.0)

# --- SIDEBAR CMD ---
with st.sidebar:
    st.header("⚡ MODE REAL TIME")
    st.warning("FORCE LIVE ACTIVE")
    p_in_set = st.number_input("TARGET IN", value=1.4440, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4460, format="%.4f")
    budget_base = st.number_input("BASE USDC", value=10.0)
    
    st.divider()
    if st.button("🚨 RESET GAINS & CYCLES", use_container_width=True):
        st.session_state.profit_total = 0.0
        for b in st.session_state.bots:
            st.session_state.bots[b]["gain"] = 0.0
            st.session_state.bots[b]["cycles"] = 0
        sauvegarder_donnees(st.session_state.bots, 0.0)
        st.rerun()
    st.divider()

    for i in range(100):
        name = f"Bot_{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"l_{i}"):
                try:
                    pa, pv = float(kraken.price_to_precision('XRP/USDC', p_in_set)), float(kraken.price_to_precision('XRP/USDC', p_out_set))
                    st.session_state.bots[name].update({"id": "LIVE", "status": "ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(e)
        else:
            if c2.button(f"OFF {i+1}", key=f"off_{i}"):
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# --- MAIN ---
live = st.empty()

while True:
    try:
        # Récupération Prix et Balance USDC réelle
        ticker = kraken.fetch_ticker('XRP/USDC')
        px = ticker['last']
        balance = kraken.fetch_balance()
        bankroll_usdc = balance.get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET FEED - XRP/USDC (LIVE)")
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL (USDC)", f"{bankroll_usdc:.2f}")
            c2.metric("XRP PRICE", f"{px:.4f}")
            c3.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            st.divider()
            
            for i in range(100):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                if bot["status"] != "LIBRE":
                    # BOULE DE NEIGE
                    val_snow = budget_base + bot['gain']
                    status_color = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                    
                    st.markdown(f'''
                    <div class="bot-line">
                        <span class="bot-id">#{i+1:02d}</span>
                        <span style="color:{status_color}; font-weight:bold;">{bot["status"]}</span>
                        <span><span class="p-in">{bot["p_achat"]}</span> → <span class="p-out">{bot["p_vente"]}</span></span>
                        <span class="flash-box">{val_snow:.2f} USDC</span>
                        <span class="flash-box">{bot["cycles"]} CYCLES</span>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # LOGIQUE LIVE
                    vol = float(kraken.amount_to_precision('XRP/USDC', val_snow / px))
                    
                    if bot["status"] == "ACHAT" and px <= bot["p_achat"]:
                        try:
                            kraken.create_limit_buy_order('XRP/USDC', vol, bot["p_achat"])
                            st.session_state.bots[name].update({"status": "VENTE"})
                            st.toast(f"LIVE BUY EXEC: Bot {i+1}")
                        except Exception as e: st.error(f"Error Buy #{i+1}: {e}")
                        
                    elif bot["status"] == "VENTE" and px >= bot["p_vente"]:
                        try:
                            kraken.create_limit_sell_order('XRP/USDC', vol, bot["p_vente"])
                            g = (bot['p_vente'] - bot['p_achat']) * vol
                            st.session_state.profit_total += g
                            st.session_state.bots[name]["gain"] += g
                            st.session_state.bots[name]["cycles"] += 1
                            st.session_state.bots[name].update({"status": "ACHAT"})
                            st.toast(f"LIVE SELL EXEC: Bot {i+1} (+{g:.2f})")
                        except Exception as e: st.error(f"Error Sell #{i+1}: {e}")
                    
                    # PAUSE ANTI-NONCE
                    time.sleep(0.05)
            
            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)

    except Exception as e:
        if "Invalid nonce" in str(e):
            st.warning("Système : Resynchronisation du Nonce...")
            time.sleep(1)
        else:
            st.write(f"SYSTEM ERROR: {str(e)[:50]}")
    
    time.sleep(5)
