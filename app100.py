import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE CLAIR ET LISIBLE
st.set_page_config(page_title="XRP Bot Standard", layout="wide")
st.markdown("""
    <style>
    /* Prix central bien visible sur fond gris clair */
    .live-price-container {
        text-align: center;
        padding: 20px;
        background: #f0f2f6;
        border: 2px solid #0070FF;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .live-price-val {
        font-size: 50px !important;
        font-weight: 900 !important;
        color: #000000;
    }
    .bot-line { 
        border-bottom: 1px solid #e6e9ef; 
        padding: 10px 0px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
    }
    .status-v { color: #28a745; font-weight: bold; } /* Vert */
    .status-a { color: #fd7e14; font-weight: bold; } /* Orange */
    .cycle-badge { background-color: #007bff; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .flash-box { background-color: #ffc107; color: black; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
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
        st.session_state.bots, st.session_state.profit_total = mem.get("bots"), mem.get("profit_total", 0.0)
    else:
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.session_state.profit_total = 0.0
    st.session_state.bankroll = 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ CMD")
    p_in_set = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    budget_val = st.number_input("BUDGET (USDC)", value=35.0)
    
    if st.button("🚨 RESET TOTAL"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.session_state.profit_total = 0.0
        sauvegarder(st.session_state.bots, 0.0); st.rerun()

    for i in range(100):
        id_b = f"B{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[id_b]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"g{i}"):
                if not kraken.markets: kraken.load_markets()
                pa_f, pv_f = float(kraken.price_to_precision('XRP/USDC', p_in_set)), float(kraken.price_to_precision('XRP/USDC', p_out_set))
                vol = float(kraken.amount_to_precision('XRP/USDC', budget_val / pa_f))
                try:
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                    st.session_state.bots[id_b].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "budget": budget_val, "oid": res['id']})
                    sauvegarder(st.session_state.bots, st.session_state.profit_total); st.rerun()
                except Exception as e: st.error(e)
        else:
            if c2.button(f"OFF {i+1}", key=f"o{i}"):
                try: 
                    if st.session_state.bots[id_b]["oid"] != "NONE": kraken.cancel_order(st.session_state.bots[id_b]["oid"])
                except: pass
                st.session_state.bots[id_b].update({"status": "LIBRE", "oid": "NONE"}); st.rerun()

# --- MAIN ---
live = st.empty()
count = 0
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        if count % 5 == 0: st.session_state.bankroll = kraken.fetch_balance().get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.markdown(f'''
                <div class="live-price-container">
                    <div style="font-size:14px; color:#555;">PRIX XRP ACTUEL (USDC)</div>
                    <div class="live-price-val">{px:.4f}</div>
                </div>
            ''', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{st.session_state.bankroll:.2f} USDC")
            c2.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            c3.metric("BOTS ON", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            st.divider()
            
            for name, bot in st.session_state.bots.items():
                if bot["status"] != "LIBRE":
                    actuel_b = bot["budget"] + bot["gain"]
                    
                    if bot["status"] == "ACHAT" and count % 2 == 0:
                        try:
                            if kraken.fetch_order(bot["oid"])['status'] == 'closed':
                                st.session_state.bots[name]["status"] = "VENTE"
                                vol = float(kraken.amount_to_precision('XRP/USDC', actuel_b / bot["pa"]))
                                v_res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["pv"])
                                st.session_state.bots[name]["oid"] = v_res['id']
                                sauvegarder(st.session_state.bots, st.session_state.profit_total)
                        except: pass

                    st_label = "VENTE" if bot["status"] == "VENTE" else "ACHAT"
                    st_class = "status-v" if bot["status"] == "VENTE" else "status-a"
                    
                    st.markdown(f'''
                        <div class="bot-line">
                            <span style="font-weight:bold;">{name}</span>
                            <span class="{st_class}">{st_label}</span>
                            <span>{bot["pa"]} → {bot["pv"]}</span>
                            <span class="cycle-badge">{bot.get("cycles", 0)} CYCLES</span>
                            <span class="flash-box">{actuel_b:.2f} USDC</span>
                        </div>''', unsafe_allow_html=True)
    except: pass
    count += 1
    time.sleep(10)
