import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. RETOUR AU STYLE "BLOOMBERG TERMINAL ULTRA" (NOIR & NÉON)
st.set_page_config(page_title="XRP Bloomberg TERMINAL", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000 !important; color: #FFFFFF; font-family: 'Courier New', monospace; }
    .stApp { background-color: #000000 !important; }
    
    /* PRIX LIVE CENTRE - LOOK NÉON VERT */
    .live-price-container {
        text-align: center;
        padding: 20px;
        background: #111111;
        border: 2px solid #00FF00;
        border-radius: 10px;
        margin-bottom: 25px;
        box-shadow: 0px 0px 15px #00FF00;
    }
    .live-price-val {
        font-size: 50px !important;
        font-weight: 900 !important;
        color: #00FF00;
        text-shadow: 0px 0px 10px #00FF00;
    }
    
    [data-testid="stMetric"] { background-color: #111111 !important; border: 1px solid #333; border-radius: 4px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 22px !important; }
    
    /* LIGNES DES BOTS */
    .bot-line { border-bottom: 1px solid #222222; padding: 12px 0px; display: flex; justify-content: space-between; align-items: center; }
    .status-v { color: #00FF00; font-weight: 900; }
    .status-a { color: #FFA500; font-weight: 900; }
    .cycle-badge { background-color: #FFFFFF; color: #000000; padding: 2px 10px; border-radius: 2px; font-weight: 900; font-size: 12px; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 2px 8px; border-radius: 2px; font-weight: 900; }
    .bot-id { color: #666; font-weight: bold; width: 45px; }
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

    for i in range(25): # Affiche les 25 premiers pour la fluidité
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
                except Exception as e: st.error(f"Kraken: {e}")
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
                    <div style="font-size:14px; color:#AAA;">XRP / USDC MARKET PRICE</div>
                    <div class="live-price-val">{px:.4f}</div>
                </div>
            ''', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{st.session_state.bankroll:.2f} USDC")
            c2.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            c3.metric("BOTS ON", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            st.divider()
            
            # AFFICHE UNIQUEMENT LES BOTS ACTIFS (POUR LA LÉGÈRETÉ)
            actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
            
            for name in actifs:
                bot = st.session_state.bots[name]
                actuel_b = bot["budget"] + bot["gain"]
                
                # VERIFICATION AUTO (Optimisée)
                if bot["status"] == "ACHAT" and count % 2 == 0:
                    try:
                        if kraken.fetch_order(bot["oid"])['status'] == 'closed':
                            st.session_state.bots[name]["status"] = "VENTE"
                            vol = float(kraken.amount_to_precision('XRP/USDC', actuel_b / bot["pa"]))
                            v_res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["pv"])
                            st.session_state.bots[name]["oid"] = v_res['id']
                            sauvegarder(st.session_state.bots, st.session_state.profit_total)
                    except: pass

                status_label = "VENTE" if bot["status"] == "VENTE" else "ACHAT"
                sc_class = "status-v" if bot["status"] == "VENTE" else "status-a"
                
                st.markdown(f'''
                    <div class="bot-line">
                        <span class="bot-id">{name}</span>
                        <span class="{sc_class}">{status_label}</span>
                        <span>{bot["pa"]} → {bot["pv"]}</span>
                        <span class="cycle-badge">{bot.get("cycles", 0)} CYCLES</span>
                        <span class="flash-box">{actuel_b:.2f} USDC</span>
                    </div>''', unsafe_allow_html=True)
    except: pass
    count += 1
    time.sleep(10)
