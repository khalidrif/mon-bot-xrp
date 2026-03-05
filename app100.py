import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE "BLOOMBERG ELITE"
st.set_page_config(page_title="XRP TERMINAL ELITE", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    
    /* HEADER PRIX CENTRAL ULTRA LOOK */
    .price-card {
        background: linear-gradient(180deg, #111 0%, #000 100%);
        border: 1px solid #333;
        border-top: 3px solid #00FF00;
        padding: 15px;
        text-align: center;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    .price-label { color: #888; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; }
    .price-value { 
        color: #00FF00; 
        font-size: 60px !important; 
        font-weight: 900; 
        text-shadow: 0px 0px 20px rgba(0, 255, 0, 0.4);
        margin: 10px 0px;
    }

    /* NET GAIN STYLE FLASHY */
    .gain-box {
        background: #002200;
        border-left: 5px solid #00FF00;
        padding: 15px;
        margin-bottom: 20px;
    }
    .gain-label { color: #00FF00; font-size: 11px; font-weight: bold; }
    .gain-value { color: #FFFFFF; font-size: 28px; font-weight: 900; }

    .bot-line { 
        border-bottom: 1px solid #1a1a1a; 
        padding: 12px 10px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        background: #050505;
        margin-bottom: 2px;
    }
    .status-v { color: #00FF00; font-weight: 900; background: rgba(0,255,0,0.1); padding: 2px 8px; border-radius: 2px; }
    .status-a { color: #FFA500; font-weight: 900; background: rgba(255,165,0,0.1); padding: 2px 8px; border-radius: 2px; }
    .cycle-badge { border: 1px solid #444; color: #AAA; padding: 2px 8px; font-size: 11px; font-weight: bold; }
    .flash-box { color: #FFFF00; font-weight: 900; font-size: 16px; }
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
    st.header("TERMINAL CONTROL")
    p_in_set = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    budget_val = st.number_input("UNIT BUDGET (USDC)", value=35.0)
    
    if st.button("🚨 PURGE ALL DATA"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.session_state.profit_total = 0.0
        sauvegarder(st.session_state.bots, 0.0); st.rerun()

    for i in range(100):
        id_b = f"B{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[id_b]["status"] == "LIBRE":
            if c1.button(f"RUN {i+1}", key=f"g{i}"):
                if not kraken.markets: kraken.load_markets()
                pa_f, pv_f = float(kraken.price_to_precision('XRP/USDC', p_in_set)), float(kraken.price_to_precision('XRP/USDC', p_out_set))
                vol = float(kraken.amount_to_precision('XRP/USDC', budget_val / pa_f))
                try:
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                    st.session_state.bots[id_b].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "budget": budget_val, "oid": res['id']})
                    sauvegarder(st.session_state.bots, st.session_state.profit_total); st.rerun()
                except Exception as e: st.error(e)
        else:
            if c2.button(f"HALT {i+1}", key=f"o{i}"):
                try: 
                    if st.session_state.bots[id_b]["oid"] != "NONE": kraken.cancel_order(st.session_state.bots[id_b]["oid"])
                except: pass
                st.session_state.bots[id_b].update({"status": "LIBRE", "oid": "NONE"}); st.rerun()

# --- MAIN INTERFACE ---
live = st.empty()
count = 0
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        if count % 5 == 0: 
            bal = kraken.fetch_balance()
            st.session_state.bankroll = bal.get('USDC', {}).get('free', 0.0)
        
        with live.container():
            # HEADER PRIX DYNAMIQUE
            st.markdown(f'''
                <div class="price-card">
                    <div class="price-label">XRP / USDC INDEX</div>
                    <div class="price-value">{px:.4f}</div>
                </div>
            ''', unsafe_allow_html=True)

            # NET GAIN FLASHY
            st.markdown(f'''
                <div class="gain-box">
                    <div class="gain-label">TOTAL ACCUMULATED PROFIT</div>
                    <div class="gain-value">+{st.session_state.profit_total:.4f} <span style="font-size:12px; color:#888;">USDC</span></div>
                </div>
            ''', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            col1.metric("ACCOUNT BALANCE", f"{st.session_state.bankroll:.2f} USDC")
            col2.metric("ACTIVE BOTS", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            
            st.write("")
            
            for name, bot in st.session_state.bots.items():
                if bot["status"] != "LIBRE":
                    actuel_b = bot["budget"] + bot["gain"]
                    
                    # LOGIQUE VERIF AUTOMATIQUE
                    if bot["status"] == "ACHAT" and count % 2 == 0:
                        try:
                            if kraken.fetch_order(bot["oid"])['status'] == 'closed':
                                st.session_state.bots[name]["status"] = "VENTE"
                                vol = float(kraken.amount_to_precision('XRP/USDC', actuel_b / bot["pa"]))
                                v_res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["pv"])
                                st.session_state.bots[name]["oid"] = v_res['id']
                                sauvegarder(st.session_state.bots, st.session_state.profit_total)
                        except: pass
                    
                    # LOGIQUE FIN DE CYCLE
                    if bot["status"] == "VENTE" and count % 2 == 0:
                        try:
                            if kraken.fetch_order(bot["oid"])['status'] == 'closed':
                                g = (bot["pv"] - bot["pa"]) * (actuel_b / bot["pa"])
                                st.session_state.profit_total += g
                                st.session_state.bots[name].update({
                                    "status": "ACHAT",
                                    "gain": bot["gain"] + g,
                                    "cycles": bot.get("cycles", 0) + 1,
                                    "oid": "NONE"
                                })
                                sauvegarder(st.session_state.bots, st.session_state.profit_total)
                        except: pass

                    # LIGNE BOT STYLE PRO
                    s_label = "SELLING" if bot["status"] == "VENTE" else "BUYING"
                    s_class = "status-v" if bot["status"] == "VENTE" else "status-a"
                    
                    st.markdown(f'''
                        <div class="bot-line">
                            <span style="font-weight:bold; color:#555;">{name}</span>
                            <span class="{s_class}">{s_label}</span>
                            <span style="color:#888;">{bot["pa"]} <span style="color:#444;">→</span> {bot["pv"]}</span>
                            <span class="cycle-badge">CYC: {bot.get("cycles", 0)}</span>
                            <span class="flash-box">{actuel_b:.2f}</span>
                        </div>''', unsafe_allow_html=True)
    except: pass
    count += 1
    time.sleep(10)
