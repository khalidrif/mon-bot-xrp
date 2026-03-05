import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. RETOUR DU STYLE "BLOOMBERG HIGH-CONTRAST"
st.set_page_config(page_title="XRP Bloomberg DIRECT LIVE", layout="wide")
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

# 2. CONNEXION ET MÉMOIRE
kraken = get_kraken_connection()
FILE_MEMOIRE = "etat_bots.json"

def sauvegarder(bots, total):
    with open(FILE_MEMOIRE, "w") as f: json.dump({"bots": bots, "profit_total": total}, f)

def charger():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

if 'bots' not in st.session_state:
    mem = charger()
    if mem:
        st.session_state.bots = mem.get("bots")
        st.session_state.profit_total = mem.get("profit_total", 0.0)
    else:
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "oid": "NONE"} for i in range(100)}
        st.session_state.profit_total = 0.0
    st.session_state.bankroll = 0.0

# --- SIDEBAR CMD ---
with st.sidebar:
    st.header("⚡ CMD DIRECT")
    p_in_set = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    budget_val = st.number_input("BUDGET (USDC)", value=35.0)
    
    if st.button("🚨 RESET TOTAL"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "oid": "NONE"} for i in range(100)}
        st.session_state.profit_total = 0.0
        sauvegarder(st.session_state.bots, 0.0); st.rerun()

    for i in range(100):
        id_b = f"B{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[id_b]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"g{i}"):
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in_set))
                pv_f = float(kraken.price_to_precision('XRP/USDC', p_out_set))
                
                # ACTION : PLACEMENT IMMEDIAT D'ORDRE
                vol = float(kraken.amount_to_precision('XRP/USDC', budget_val / pa_f))
                try:
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                    st.session_state.bots[id_b].update({"status": "ACHAT_OUVERT", "pa": pa_f, "pv": pv_f, "budget": budget_val, "oid": res['id']})
                    sauvegarder(st.session_state.bots, st.session_state.profit_total)
                    st.toast(f"✅ ORDRE {id_b} PLACÉ : {res['id']}")
                    st.rerun()
                except Exception as e: st.error(f"KRAKEN REFUS : {e}")
        else:
            if c2.button(f"OFF {i+1}", key=f"o{i}"):
                # Annulation automatique de l'ordre sur Kraken
                try:
                    if st.session_state.bots[id_b]["oid"] != "NONE":
                        kraken.cancel_order(st.session_state.bots[id_b]["oid"])
                except: pass
                st.session_state.bots[id_b].update({"status": "LIBRE", "oid": "NONE"}); st.rerun()

# --- MAIN LOOP ---
live = st.empty()
count = 0

while True:
    try:
        ticker = kraken.fetch_ticker('XRP/USDC')
        px = ticker['last']
        if count % 5 == 0:
            bal = kraken.fetch_balance()
            st.session_state.bankroll = bal.get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET FEED : {px:.4f}")
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{st.session_state.bankroll:.2f} USDC")
            c2.metric("XRP PRICE", f"{px:.4f}")
            c3.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            st.divider()
            
            actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
            for name in actifs:
                bot = st.session_state.bots[name]
                actuel_b = bot["budget"] + bot["gain"]
                
                # DIAGNOSTIC RAPIDE
                if bot["status"] == "ACHAT_OUVERT":
                    status_txt = "OUVERT"
                    sc = "#FFA500" # Orange
                else:
                    status_txt = "ACTIF"
                    sc = "#00FF00" # Vert
                
                # Logic de bascule automatique si prix touché
                if bot["status"] == "ACHAT_OUVERT" and px <= bot["pa"]:
                    st.session_state.bots[name]["status"] = "SURVEILLANCE_VENTE"
                    sauvegarder(st.session_state.bots, st.session_state.profit_total)

                st.markdown(f'''
                    <div class="bot-line">
                        <span class="bot-id">{name}</span>
                        <span style="color:{sc}; font-weight:bold;">{status_txt}</span>
                        <span><span class="p-in">{bot["pa"]}</span> → <span class="p-out">{bot["pv"]}</span></span>
                        <span class="flash-box">{actuel_b:.2f} USDC</span>
                    </div>''', unsafe_allow_html=True)
                
    except: pass
    count += 1
    time.sleep(10)
