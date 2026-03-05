import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE "BLOOMBERG ORIGINAL" (FONDS NOIR / FLASH JAUNE)
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

# 2. MÉMOIRE ET CONNEXION
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
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "cycles": 0, "oid": "NONE"} for i in range(100)}
        st.session_state.profit_total = 0.0
    st.session_state.bankroll = 0.0

# --- SIDEBAR CMD ---
with st.sidebar:
    st.header("⚡ CMD TERMINAL")
    p_in_set = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    budget_val = st.number_input("BASE USDC (MIN 35)", value=35.0)
    
    if st.button("🚨 RESET TOTAL DATA"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "cycles": 0, "oid": "NONE"} for i in range(100)}
        st.session_state.profit_total = 0.0
        sauvegarder_donnees(st.session_state.bots, 0.0); st.rerun()

    for i in range(25): # On limite l'affichage sidebar pour la fluidité
        id_b = f"B{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[id_b]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"g{i}"):
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in_set))
                pv_f = float(kraken.price_to_precision('XRP/USDC', p_out_set))
                vol = float(kraken.amount_to_precision('XRP/USDC', budget_val / pa_f))
                try:
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                    st.session_state.bots[id_b].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "budget": budget_val, "oid": res['id']})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total); st.rerun()
                except Exception as e: st.error(f"Kraken: {e}")
        else:
            if c2.button(f"OFF {i+1}", key=f"o{i}"):
                st.session_state.bots[id_b]["status"] = "LIBRE"; st.rerun()

# --- MAIN LOOP ---
live = st.empty()
count = 0
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        if count % 5 == 0: st.session_state.bankroll = kraken.fetch_balance().get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET FEED : {px:.4f} XRP/USDC")
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{st.session_state.bankroll:.2f} USDC")
            c2.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            c3.metric("BOTS ACTIFS", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            st.divider()
            
            for name, bot in st.session_state.bots.items():
                if bot["status"] != "LIBRE":
                    actuel_b = bot["budget"] + bot["gain"]
                    
                    # VERIFICATION AUTO ORDRE REMPLI
                    if bot["status"] == "ACHAT" and count % 2 == 0:
                        try:
                            if kraken.fetch_order(bot["oid"])['status'] == 'closed':
                                st.session_state.bots[name]["status"] = "VENTE"
                                vol = float(kraken.amount_to_precision('XRP/USDC', actuel_b / bot["pa"]))
                                v_res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["pv"])
                                st.session_state.bots[name]["oid"] = v_res['id']
                                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                        except: pass

                    st_label = "VENTE" if bot["status"] == "VENTE" else "ACHAT"
                    sc_color = "#00FF00" if bot["status"] == "VENTE" else "#FFA500"
                    
                    st.markdown(f'''
                        <div class="bot-line">
                            <span class="bot-id">{name}</span>
                            <span style="color:{sc_color}; font-weight:bold;">{st_label}</span>
                            <span>{bot["pa"]} → {bot["pv"]}</span>
                            <span class="flash-box">{bot.get("cycles", 0)} CYC</span>
                            <span class="flash-box">{actuel_b:.2f} USDC</span>
                        </div>''', unsafe_allow_html=True)
    except: pass
    count += 1
    time.sleep(10)
