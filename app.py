import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os

# --- 1. CONFIGURATION CONNEXION (Ex-config.py intégré) ---
def get_kraken_connection():
    # Nettoyage automatique des clés (.strip()) pour l'erreur "Incorrect padding"
    api_key = st.secrets.get("API_KEY", "").strip()
    api_secret = st.secrets.get("API_SECRET", "").strip()
    
    if not api_key or not api_secret:
        st.error("⚠️ CLÉS API MANQUANTES : Configurez les 'Secrets' dans Streamlit Cloud.")
        st.stop()

    exchange = ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'nonce': lambda: int(time.time() * 1000)}
    })
    
    # Sécurité anti "Markets not loaded"
    try:
        if not exchange.markets:
            exchange.load_markets()
    except:
        pass
    return exchange

# --- 2. STYLE BLOOMBERG ---
st.set_page_config(page_title="XRP Bloomberg Terminal", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    [data-testid="stMetric"] { background-color: #FFFF00 !important; border-radius: 5px; padding: 10px; border: 1px solid #333; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 28px !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 11px !important; font-weight: bold !important; }
    .bot-line { border-bottom: 1px solid #222222; padding: 10px 0px; display: flex; justify-content: space-between; align-items: center; }
    .p-in { color: #00FF00; font-weight: bold; }
    .p-out { color: #FF0000; font-weight: bold; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 3px 8px; border-radius: 2px; font-weight: 900; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MÉMOIRE ET ÉTAT ---
FILE_MEMOIRE = "etat_bots.json"
SYMBOL = 'XRP/USDC'

def sauvegarder_donnees(bots, profit_total):
    try:
        with open(FILE_MEMOIRE, "w") as f: 
            json.dump({"bots": bots, "profit_total": profit_total}, f)
    except: pass

def charger_donnees():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

# Initialisation
kraken = get_kraken_connection()
memoire = charger_donnees()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
    st.session_state.profit_total = 0.0
    if memoire:
        st.session_state.bots.update(memoire.get("bots", {}))
        st.session_state.profit_total = memoire.get("profit_total", 0.0)

# --- 4. SIDEBAR CMD ---
with st.sidebar:
    st.header("⚡ TERMINAL CMD")
    mode_reel = st.toggle("LIVE TRADING", value=True)
    p_in_set = st.number_input("TARGET IN", value=1.4440, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4460, format="%.4f")
    budget_base = st.number_input("BASE USD", value=10.0)
    
    st.divider()
    for i in range(10):
        name = f"Bot_{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"on_{i}"):
                try:
                    # FORCE LOAD MARKETS AU CLIC
                    if not kraken.markets: kraken.load_markets()
                    
                    montant = budget_base + st.session_state.bots[name]["gain"]
                    pa = float(kraken.price_to_precision(SYMBOL, p_in_set))
                    pv = float(kraken.price_to_precision(SYMBOL, p_out_set))
                    qty = float(kraken.amount_to_precision(SYMBOL, montant / pa))
                    
                    params = {'validate': not mode_reel}
                    res = kraken.create_order(SYMBOL, 'limit', 'buy', qty, pa, params)
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(f"Err: {str(e)[:45]}")
        else:
            if c2.button(f"OFF {i+1}", key=f"off_{i}"):
                try:
                    if st.session_state.bots[name]["id"]: kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# --- 5. LOGIQUE LIVE ---
live = st.empty()

while True:
    try:
        # Rafraîchir marchés et données
        if not kraken.markets: kraken.load_markets()
        ticker = kraken.fetch_ticker(SYMBOL)
        px = ticker['last']
        bal = kraken.fetch_balance()
        usdc_total = bal.get('total', {}).get('USDC', 0.0)

        with live.container():
            st.write(f"### 🌐 TERMINAL XRP/USDC")
            k1, k2, k3 = st.columns(3)
            k1.metric("USDC TOTAL", f"{usdc_total:.2f} $")
            k2.metric("PRIX ACTUEL", f"{px:.4f}")
            k3.metric("GAINS NETS", f"+{st.session_state.profit_total:.4f} $")
            st.divider()
            
            for i in range(10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                if bot["status"] != "LIBRE" and bot["id"]:
                    color = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                    st.markdown(f'''
                    <div class="bot-line">
                        <span style="color:#666">BOT {i+1:02d}</span>
                        <span style="color:{color}; font-weight:bold;">{bot["status"]}</span>
                        <span>{bot["p_achat"]} → {bot["p_vente"]}</span>
                        <span class="flash-box">{budget_base + bot['gain']:.2f}$</span>
                        <span class="flash-box">CYC: {bot["cycles"]}</span>
                    </div>''', unsafe_allow_html=True)
                    
                    # Logique Automatique
                    order = kraken.fetch_order(bot['id'], SYMBOL)
                    if order['status'] == 'closed':
                        params = {'validate': not mode_reel}
                        if bot["status"] == "ACHAT":
                            res = kraken.create_order(SYMBOL, 'limit', 'sell', order['filled'], bot['p_vente'], params)
                            st.session_state.bots[name].update({"id": res['id'], "status": "VENTE"})
                        else:
                            gain = (bot['p_vente'] - bot['p_achat']) * order['filled']
                            st.session_state.profit_total += gain
                            st.session_state.bots[name]["gain"] += gain
                            st.session_state.bots[name]["cycles"] += 1
                            # Relance
                            nm = budget_base + st.session_state.bots[name]["gain"]
                            nq = float(kraken.amount_to_precision(SYMBOL, nm / bot['p_achat']))
                            res = kraken.create_order(SYMBOL, 'limit', 'buy', nq, bot['p_achat'], params)
                            st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT"})
                        
                        sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                        st.rerun()

    except Exception as e:
        if "nonce" in str(e).lower(): time.sleep(1)
        else: st.caption(f"Status : {str(e)[:40]}")
    
    time.sleep(15)
