import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE BLOOMBERG
st.set_page_config(page_title="XRP Bloomberg FINAL", layout="wide")
st.markdown("<style>.main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }</style>", unsafe_allow_html=True)

# 2. CONNEXION
kraken = get_kraken_connection()
FILE_MEMOIRE = "etat_bots.json"

def sauvegarder_donnees(bots, profit_total):
    with open(FILE_MEMOIRE, "w") as f: json.dump({"bots": bots, "profit_total": profit_total}, f)

def charger_donnees():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

if 'bots' not in st.session_state:
    memoire = charger_donnees()
    if memoire:
        st.session_state.bots = memoire.get("bots")
        st.session_state.profit_total = memoire.get("profit_total", 0.0)
    else:
        st.session_state.bots = {f"Bot_{i+1}": {"status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "budget": 35.0, "gain": 0.0, "last_id": "NONE"} for i in range(100)}
        st.session_state.profit_total = 0.0
    st.session_state.bankroll = 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ CMD")
    p_in_val = st.number_input("TARGET IN", value=1.4440, format="%.4f")
    p_out_val = st.number_input("TARGET OUT", value=1.4460, format="%.4f")
    budget_val = st.number_input("BUDGET UNITAIRE", value=35.0)
    
    if st.button("🚨 RESET TOTAL"):
        st.session_state.profit_total = 0.0
        st.session_state.bots = {f"Bot_{i+1}": {"status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "budget": 35.0, "gain": 0.0, "last_id": "NONE"} for i in range(100)}
        sauvegarder_donnees(st.session_state.bots, 0.0); st.rerun()

    for i in range(100):
        name = f"Bot_{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"g{i}"):
                if not kraken.markets: kraken.load_markets()
                pa = float(kraken.price_to_precision('XRP/USDC', p_in_val))
                pv = float(kraken.price_to_precision('XRP/USDC', p_out_val))
                # ON ANCRE LE BUDGET ET LES PRIX ICI
                st.session_state.bots[name].update({"status": "ACHAT", "p_achat": pa, "p_vente": pv, "budget": budget_val})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total); st.rerun()
        else:
            if c2.button(f"OFF {i+1}", key=f"o{i}"):
                st.session_state.bots[name]["status"] = "LIBRE"; st.rerun()

# --- BOUCLE PRINCIPALE ---
live = st.empty()
while True:
    try:
        if not kraken.markets: kraken.load_markets()
        ticker = kraken.fetch_ticker('XRP/USDC')
        px = ticker['last']
        bal = kraken.fetch_balance()
        bankroll = bal.get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET: {px:.4f} | BANKROLL: {bankroll:.2f} USDC")
            
            actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
            for name in actifs:
                bot = st.session_state.bots[name]
                current_budget = bot["budget"] + bot["gain"] # Boule de neige
                vol = float(kraken.amount_to_precision('XRP/USDC', current_budget / px))
                
                if bot["status"] == "ACHAT":
                    if px <= bot["p_achat"]:
                        try:
                            order = kraken.create_limit_buy_order('XRP/USDC', vol, bot["p_achat"])
                            st.session_state.bots[name]["status"] = "VENTE"
                            st.session_state.bots[name]["last_id"] = order['id']
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.success(f"ORDRE {name} ENVOYÉ")
                        except Exception as e: st.error(f"KRAKEN {name}: {e}")
                
                elif bot["status"] == "VENTE":
                    if px >= bot["p_vente"]:
                        try:
                            order = kraken.create_limit_sell_order('XRP/USDC', vol, bot["p_vente"])
                            g = (bot["p_vente"] - bot["p_achat"]) * vol
                            st.session_state.profit_total += g
                            st.session_state.bots[name].update({"status": "ACHAT", "gain": bot["gain"]+g, "last_id": order['id']})
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.success(f"VENTE {name} RÉUSSIE")
                        except Exception as e: st.error(f"KRAKEN {name}: {e}")

                # Affichage
                st.write(f"#{name} | {bot['status']} | {bot['p_achat']} -> {bot['p_vente']} | {current_budget:.2f} USDC")
                time.sleep(0.1)

    except Exception as e: st.write(f"SYS: {e}")
    time.sleep(10)
