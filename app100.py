import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE BLOOMBERG ORIGINAL (STRICT 100 LIGNES)
st.set_page_config(page_title="XRP 100 BOTS TERMINAL", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000 !important; color: #FFFFFF; font-family: 'Courier New', monospace; }
    .stApp { background-color: #000000 !important; }
    [data-testid="stMetric"] { background-color: #FFFFFF !important; border-radius: 4px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 20px !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 12px !important; font-weight: bold !important; }
    .bot-line { border-bottom: 1px solid #1a1a1a; padding: 8px 0px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
    .status-v { color: #00FF00; font-weight: bold; }
    .status-a { color: #FFA500; font-weight: bold; }
    .status-idle { color: #333333; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 2px 6px; border-radius: 2px; font-weight: 900; font-size: 12px; }
    .bot-id { color: #555555; font-weight: bold; width: 45px; }
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
    # INITIALISATION FORCÉE DE 100 BOTS
    st.session_state.bots = mem.get("bots") if mem else {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
    st.session_state.profit_total = mem.get("profit_total", 0.0) if mem else 0.0
    st.session_state.bankroll = 0.0

# --- SIDEBAR CMD ---
with st.sidebar:
    st.header("⚡ CMD 100 BOTS")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET (USDC)", value=25.0)
    
    if st.button("🚨 RESET TOTAL DATA"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.session_state.profit_total = 0.0
        sauvegarder(st.session_state.bots, 0.0); st.rerun()

    st.write("---")
    # Liste des 100 boutons dans la barre latérale
    for i in range(100):
        name = f"B{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"g{i}"):
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                pv_f = float(kraken.price_to_precision('XRP/USDC', p_out))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                try:
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                    st.session_state.bots[name].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "budget": b_val, "oid": res['id']})
                    sauvegarder(st.session_state.bots, st.session_state.profit_total); st.rerun()
                except Exception as e: st.error(f"Erreur Kraken")
        else:
            if c2.button(f"OFF {i+1}", key=f"o{i}"):
                st.session_state.bots[name].update({"status": "LIBRE", "oid": "NONE"}); st.rerun()

# --- MAIN LOOP (AFFICHAGE DES 100 LIGNES) ---
live = st.empty()
count = 0
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        if count % 5 == 0:
            bal = kraken.fetch_balance()
            st.session_state.bankroll = bal.get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET FEED : {px:.4f} XRP/USDC")
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{st.session_state.bankroll:.2f} USDC")
            c2.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            c3.metric("BOTS ON", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            st.divider()
            
            # AFFICHAGE DE CHAQUE BOT DE 1 A 100
            for i in range(100):
                name = f"B{i+1}"
                bot = st.session_state.bots[name]
                
                # Logique de mise à jour automatique si le bot travaille
                if bot["status"] != "LIBRE" and count % 2 == 0:
                    try:
                        info = kraken.fetch_order(bot["oid"])
                        if info['status'] == 'closed':
                            if bot["status"] == "ACHAT":
                                st.session_state.bots[name]["status"] = "VENTE"
                                vol = float(kraken.amount_to_precision('XRP/USDC', (bot["budget"]+bot["gain"]) / bot["pa"]))
                                v_res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["pv"])
                                st.session_state.bots[name]["oid"] = v_res['id']
                            else:
                                g = (bot["pv"] - bot["pa"]) * (bot["budget"] / bot["pa"])
                                st.session_state.profit_total += g
                                st.session_state.bots[name].update({"status": "ACHAT", "gain": bot["gain"]+g, "cycles": bot["cycles"]+1})
                            sauvegarder(st.session_state.bots, st.session_state.profit_total)
                    except: pass

                # COULEURS ET LABELS
                if bot["status"] == "LIBRE":
                    st_label, st_class = "IDLE", "status-idle"
                    pa_v, pv_v, cash_v = "---", "---", "0.00 $"
                else:
                    st_label = bot["status"]
                    st_class = "status-v" if st_label == "VENTE" else "status-a"
                    pa_v, pv_v = f"{bot['pa']:.4f}", f"{bot['pv']:.4f}"
                    cash_v = f"{bot['budget'] + bot['gain']:.2f} $"

                # AFFICHAGE DE LA LIGNE
                st.markdown(f'''
                    <div class="bot-line">
                        <span class="bot-id">{name}</span>
                        <span class="{st_class}">{st_label}</span>
                        <span style="color:#555;">{pa_v} → {pv_v}</span>
                        <span class="flash-box">{bot.get("cycles", 0)} CYC</span>
                        <span class="flash-box">{cash_v}</span>
                    </div>''', unsafe_allow_html=True)
                
    except Exception as e: pass
    count += 1
    time.sleep(10)
