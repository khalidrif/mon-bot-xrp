import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os

# --- CONFIGURATION CONNEXION ---
def get_kraken_connection():
    # Utilise les Secrets de Streamlit Cloud ou des valeurs par défaut en local
    api_key = st.secrets.get("API_KEY", "VOTRE_CLE_ICI")
    api_secret = st.secrets.get("API_SECRET", "VOTRE_SECRET_ICI")
    
    exchange = ccxt.kraken({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'nonce': lambda: int(time.time() * 1000)}
    })
    return exchange

# --- STYLE BLOOMBERG ---
st.set_page_config(page_title="XRP Bloomberg Terminal", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    [data-testid="stMetric"] { background-color: #FFFF00 !important; border-radius: 5px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 30px !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 12px !important; font-weight: bold !important; }
    .bot-line { border-bottom: 1px solid #222222; padding: 8px 0px; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
    .p-in { color: #00FF00; font-weight: bold; }
    .p-out { color: #FF0000; font-weight: bold; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 2px 6px; border-radius: 2px; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION ---
FILE_MEMOIRE = "etat_bots.json"

def sauvegarder_donnees(bots, profit_total):
    with open(FILE_MEMOIRE, "w") as f: 
        json.dump({"bots": bots, "profit_total": profit_total}, f)

def charger_donnees():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

# Connexion et chargement des marchés (Crucial pour éviter l'erreur)
kraken = get_kraken_connection()
try:
    kraken.load_markets()
except Exception as e:
    st.error(f"Erreur Kraken : {e}")

memoire = charger_donnees()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
    st.session_state.profit_total = 0.0
    if memoire:
        st.session_state.bots.update(memoire["bots"])
        st.session_state.profit_total = memoire.get("profit_total", 0.0)

# --- SIDEBAR CMD ---
with st.sidebar:
    st.header("TERMINAL CMD")
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
                    qty = (budget_base + st.session_state.bots[name]["gain"]) / p_in_set
                    pa = float(kraken.price_to_precision('XRP/USDC', p_in_set))
                    pv = float(kraken.price_to_precision('XRP/USDC', p_out_set))
                    res = kraken.create_order('XRP/USDC', 'limit', 'buy', float(kraken.amount_to_precision('XRP/USDC', qty)), pa, {'validate': not mode_reel})
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(f"Erreur Bot {i+1}: {e}")
        else:
            if c2.button(f"OFF {i+1}", key=f"off_{i}"):
                try:
                    kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# --- BOUCLE PRINCIPALE ---
live = st.empty()

while True:
    try:
        # Fetch Market Info
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        px = (float(ob['asks'][0][0]) + float(ob['bids'][0][0])) / 2
        bal = kraken.fetch_balance()
        usdc = bal.get('free', {}).get('USDC', 0)

        with live.container():
            st.write(f"### MARKET FEED - XRP/USDC")
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{usdc:.2f} $")
            c2.metric("XRP PRICE", f"{px:.4f}")
            c3.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            st.divider()
            
            for i in range(10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                if bot["status"] != "LIBRE":
                    status_color = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                    st.markdown(f'''
                    <div class="bot-line">
                        <span style="color:#555">#{i+1:02d}</span>
                        <span style="color:{status_color}; font-weight:bold;">{bot["status"]}</span>
                        <span><span class="p-in">{bot["p_achat"]}</span> → <span class="p-out">{bot["p_vente"]}</span></span>
                        <span class="flash-box">{budget_base + bot['gain']:.2f}$</span>
                        <span class="flash-box">CYC:{bot["cycles"]}</span>
                    </div>''', unsafe_allow_html=True)
                    
                    # Logique de trading
                    info = kraken.fetch_order(bot['id'], 'XRP/USDC')
                    if info['status'] == 'closed':
                        if bot["status"] == "ACHAT":
                            res = kraken.create_order('XRP/USDC', 'limit', 'sell', info['filled'], bot['p_vente'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res['id'], "status": "VENTE"})
                        else:
                            gain_cycle = (bot['p_vente'] - bot['p_achat']) * info['filled']
                            st.session_state.profit_total += gain_cycle
                            st.session_state.bots[name]["gain"] += gain_cycle
                            st.session_state.bots[name]["cycles"] += 1
                            # Relance auto de l'achat (Compounding)
                            new_q = (budget_base + st.session_state.bots[name]["gain"]) / bot['p_achat']
                            res = kraken.create_order('XRP/USDC', 'limit', 'buy', float(kraken.amount_to_precision('XRP/USDC', new_q)), bot['p_achat'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT"})
                            
                        sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                        st.rerun()

    except Exception as e:
        st.caption(f"Système en attente (API)... {str(e)[:30]}")
    
    time.sleep(15) # Refresh toutes les 15s
