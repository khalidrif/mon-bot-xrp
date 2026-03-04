import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os

# --- 1. CONFIGURATION ET CONNEXION SÉCURISÉE ---
def get_kraken_connection():
    # .strip() est INDISPENSABLE pour corriger l'erreur "Incorrect padding"
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
    
    # Correction erreur "Markets not loaded"
    try:
        exchange.load_markets()
    except Exception as e:
        st.error(f"Erreur Sync Marchés : {e}")
    return exchange

# --- 2. STYLE BLOOMBERG HIGH-CONTRAST ---
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

kraken = get_kraken_connection()
memoire = charger_donnees()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
    st.session_state.profit_total = 0.0
    if memoire:
        st.session_state.bots.update(memoire.get("bots", {}))
        st.session_state.profit_total = memoire.get("profit_total", 0.0)

# --- 4. PANNEAU LATÉRAL (COMMANDES) ---
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
                    montant = budget_base + st.session_state.bots[name]["gain"]
                    qty = montant / p_in_set
                    pa = float(kraken.price_to_precision('XRP/USDC', p_in_set))
                    pv = float(kraken.price_to_precision('XRP/USDC', p_out_set))
                    res = kraken.create_order('XRP/USDC', 'limit', 'buy', float(kraken.amount_to_precision('XRP/USDC', qty)), pa, {'validate': not mode_reel})
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(f"Erreur: {str(e)[:50]}")
        else:
            if c2.button(f"OFF {i+1}", key=f"off_{i}"):
                try:
                    if st.session_state.bots[name]["id"]:
                        kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# --- 5. AFFICHAGE ET LOGIQUE TRADING ---
live = st.empty()

while True:
    try:
        # Données Marché
        ticker = kraken.fetch_ticker('XRP/USDC')
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
                if bot["status"] != "LIBRE":
                    color = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                    st.markdown(f'''
                    <div class="bot-line">
                        <span style="color:#666">BOT {i+1:02d}</span>
                        <span style="color:{color}; font-weight:bold;">{bot["status"]}</span>
                        <span>{bot["p_achat"]} → {bot["p_vente"]}</span>
                        <span class="flash-box">BUDGET: {budget_base + bot['gain']:.2f}$</span>
                        <span class="flash-box">CYC: {bot["cycles"]}</span>
                    </div>''', unsafe_allow_html=True)
                    
                    # Vérification des ordres
                    if bot["id"]:
                        order = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        if order['status'] == 'closed':
                            if bot["status"] == "ACHAT":
                                # Passer à la vente
                                res = kraken.create_order('XRP/USDC', 'limit', 'sell', order['filled'], bot['p_vente'], {'validate': not mode_reel})
                                st.session_state.bots[name].update({"id": res['id'], "status": "VENTE"})
                            else:
                                # Vente terminée -> Profit & Relance
                                gain = (bot['p_vente'] - bot['p_achat']) * order['filled']
                                st.session_state.profit_total += gain
                                st.session_state.bots[name]["gain"] += gain
                                st.session_state.bots[name]["cycles"] += 1
                                
                                # Relance AUTO (Compounding)
                                new_m = budget_base + st.session_state.bots[name]["gain"]
                                new_q = float(kraken.amount_to_precision('XRP/USDC', new_m / bot['p_achat']))
                                res = kraken.create_order('XRP/USDC', 'limit', 'buy', new_q, bot['p_achat'], {'validate': not mode_reel})
                                st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT"})
                                
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.rerun()

    except Exception as e:
        if "nonce" in str(e).lower():
            time.sleep(1)
        else:
            st.caption(f"Système en attente... {str(e)[:40]}")
    
    time.sleep(15)
