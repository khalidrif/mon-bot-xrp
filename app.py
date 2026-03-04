import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os
from config import get_kraken_connection

# --- 1. STYLE "TERMINAL NOIR" (BLINDÉ) ---
st.set_page_config(page_title="XRP Terminal", layout="wide")

# Injection CSS pour forcer le noir partout et stopper les sauts d'écran
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    
    /* Metrics Jaunes */
    [data-testid="stMetric"] { 
        background-color: #FFFF00 !important; 
        border-radius: 5px; padding: 15px; border: 1px solid #333;
    }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 24px !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 10px !important; }

    /* Lignes des bots */
    .bot-line { 
        border-bottom: 1px solid #222222; 
        padding: 10px 0px; 
        display: flex; justify-content: space-between; align-items: center;
        min-height: 50px;
    }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 3px 8px; border-radius: 2px; font-weight: 900; }
    
    /* Masquer les éléments de chargement qui font clignoter */
    [data-testid="stStatusWidget"] { display: none !important; }
    .stDeployButton { display:none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIQUE MÉMOIRE ---
FILE_MEMOIRE = "etat_bots.json"
SYMBOL = 'XRP/USDC'

def charger_donnees():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

def sauvegarder_donnees(bots, profit_total):
    try:
        with open(FILE_MEMOIRE, "w") as f: 
            json.dump({"bots": bots, "profit_total": profit_total}, f)
    except: pass

# --- 3. INITIALISATION ---
kraken = get_kraken_connection()
memoire = charger_donnees()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
    st.session_state.profit_total = 0.0
    if memoire:
        st.session_state.bots.update(memoire.get("bots", {}))
        st.session_state.profit_total = memoire.get("profit_total", 0.0)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚡ CMD CENTER")
    if st.button("🔄 REFRESH PRIX", use_container_width=True): st.rerun()
    st.divider()
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
                    if not kraken.markets: kraken.load_markets()
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

# --- 5. DASHBOARD STATIQUE ---
try:
    ticker = kraken.fetch_ticker(SYMBOL)
    px = ticker['last']
    bal = kraken.fetch_balance()
    usdc = bal.get('total', {}).get('USDC', 0.0)

    st.write(f"### 🌐 TERMINAL STABLE - {SYMBOL}")
    k1, k2, k3 = st.columns(3)
    k1.metric("BANKROLL", f"{usdc:.2f} $")
    k2.metric("XRP PRICE", f"{px:.4f}")
    k3.metric("TOTAL NET", f"+{st.session_state.profit_total:.4f}")
    st.divider()

    for i in range(10):
        name = f"Bot_{i+1}"
        bot = st.session_state.bots[name]
        if bot["status"] != "LIBRE" and bot["id"]:
            color = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
            st.markdown(f'''
            <div class="bot-line">
                <span style="color:#666">#{i+1:02d}</span>
                <span style="color:{color}; font-weight:bold;">{bot["status"]}</span>
                <span>{bot["p_achat"]} → {bot["p_vente"]}</span>
                <span class="flash-box">{budget_base + bot['gain']:.2f}$</span>
            </div>''', unsafe_allow_html=True)
            
            # Check Order (Silencieux)
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
                    nq = float(kraken.amount_to_precision(SYMBOL, (budget_base + st.session_state.bots[name]["gain"]) / bot['p_achat']))
                    res = kraken.create_order(SYMBOL, 'limit', 'buy', nq, bot['p_achat'], params)
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT"})
                
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

except Exception as e:
    st.caption(f"Sync en cours...")

# AUTO-REFRESH SANS CLIGNOTEMENT (Injection JS)
import streamlit.components.v1 as components
components.html(
    """<script>
    setTimeout(function() { window.parent.document.dispatchEvent(new CustomEvent('streamlit:setComponentValue', {detail: {value: true, key: 'r'}})); }, 20000);
    </script>""", height=0
)
