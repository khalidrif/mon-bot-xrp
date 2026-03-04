import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os
from config import get_kraken_connection

# --- 1. STYLE FIXE (BLOQUE LA VAGUE) ---
st.set_page_config(page_title="XRP Terminal Stable", layout="wide")

st.markdown("""
    <style>
    /* Fixe le fond et empêche les sauts */
    .stApp { background-color: #F0F2F6 !important; }
    [data-testid="stAppViewContainer"] { overflow: hidden; }
    
    /* Metrics Jaunes Stables */
    [data-testid="stMetric"] { 
        background-color: #FFFF00 !important; 
        border-radius: 8px; padding: 15px; border: 2px solid #000;
        min-height: 110px;
    }
    [data-testid="stMetricValue"] { color: #000 !important; font-size: 26px !important; font-weight: 900 !important; }
    
    /* Lignes des bots qui ne bougent pas */
    .bot-line { 
        background-color: #FFFFFF; border-radius: 5px; margin-bottom: 4px;
        padding: 10px; display: flex; justify-content: space-between; border: 1px solid #DDD;
        min-height: 45px;
    }
    .flash-box { background-color: #FFFF00; color: #000; padding: 2px 6px; font-weight: 900; border: 1px solid #000; }
    
    /* Cache l'icône de chargement */
    [data-testid="stStatusWidget"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INIT ---
SYMBOL = 'XRP/USDC'
FILE_MEMOIRE = "etat_bots.json"

def charger_donnees():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

def sauvegarder_donnees(bots, profit_total):
    try:
        with open(FILE_MEMOIRE, "w") as f: json.dump({"bots": bots, "profit_total": profit_total}, f)
    except: pass

kraken = get_kraken_connection()
memoire = charger_donnees()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
    st.session_state.profit_total = 0.0
    if memoire:
        st.session_state.bots.update(memoire.get("bots", {}))
        st.session_state.profit_total = memoire.get("profit_total", 0.0)

# --- 3. SIDEBAR (CONTROLE) ---
with st.sidebar:
    st.header("⚙️ CONFIG")
    mode_reel = st.toggle("LIVE TRADING", value=True)
    p_in_set = st.number_input("TARGET IN", value=1.4440, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4460, format="%.4f")
    budget_base = st.number_input("BASE USD", value=10.0)
    st.divider()
    for i in range(10):
        name = f"Bot_{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"go_{i}"):
                try:
                    pa = float(kraken.price_to_precision(SYMBOL, p_in_set))
                    pv = float(kraken.price_to_precision(SYMBOL, p_out_set))
                    qty = float(kraken.amount_to_precision(SYMBOL, (budget_base + st.session_state.bots[name]["gain"]) / pa))
                    res = kraken.create_order(SYMBOL, 'limit', 'buy', qty, pa, {'validate': not mode_reel})
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(f"Err {i+1}")
        else:
            if c2.button(f"OFF {i+1}", key=f"off_{i}"):
                try:
                    if st.session_state.bots[name]["id"]: kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# --- 4. DASHBOARD (SANS BOUCLE STREAMLIT) ---
try:
    ticker = kraken.fetch_ticker(SYMBOL)
    px = ticker['last']
    bal = kraken.fetch_balance()
    usdc = bal.get('total', {}).get('USDC', 0.0)

    st.write(f"## 🏛️ TERMINAL STABLE - {SYMBOL}")
    k1, k2, k3 = st.columns(3)
    k1.metric("SOLDE USDC", f"{usdc:.2f} $")
    k2.metric("PRIX XRP", f"{px:.4f}")
    k3.metric("GAINS NETS", f"+{st.session_state.profit_total:.4f} $")
    st.divider()

    # Monitoring des Bots
    for i in range(10):
        name = f"Bot_{i+1}"
        bot = st.session_state.bots[name]
        if bot["status"] != "LIBRE" and bot["id"]:
            color = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
            st.markdown(f'''
            <div class="bot-line">
                <span style="font-weight:bold;">BOT {i+1:02d}</span>
                <span style="color:{color}; font-weight:bold;">{bot["status"]}</span>
                <span>{bot["p_achat"]} ➔ {bot["p_vente"]}</span>
                <span class="flash-box">{budget_base + bot['gain']:.2f}$</span>
            </div>''', unsafe_allow_html=True)
            
            # Vérification des ordres
            order = kraken.fetch_order(bot['id'], SYMBOL)
            if order['status'] == 'closed':
                if bot["status"] == "ACHAT":
                    res = kraken.create_order(SYMBOL, 'limit', 'sell', order['filled'], bot['p_vente'])
                    st.session_state.bots[name].update({"id": res['id'], "status": "VENTE"})
                else:
                    # Boule de neige
                    gain = (bot['p_vente'] - bot['p_achat']) * order['filled']
                    st.session_state.profit_total += gain
                    st.session_state.bots[name]["gain"] += gain
                    st.session_state.bots[name]["cycles"] += 1
                    nq = float(kraken.amount_to_precision(SYMBOL, (budget_base + st.session_state.bots[name]["gain"]) / bot['p_achat']))
                    res = kraken.create_order(SYMBOL, 'limit', 'buy', nq, bot['p_achat'])
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

except Exception as e:
    st.caption("Synchronisation...")

# --- 5. LE SECRET : RAFRAICHISSEMENT JAVASCRIPT ---
# Rafraîchit la page toutes les 10 secondes proprement sans faire de vague
import streamlit.components.v1 as components
components.html(
    """
    <script>
    setTimeout(function() {
        window.parent.document.dispatchEvent(new CustomEvent('streamlit:setComponentValue', {detail: {value: true, key: 'r'}}));
    }, 10000); // 10 secondes
    </script>
    """,
    height=0,
)
