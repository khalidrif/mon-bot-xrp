import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE BLOOMBERG ORIGINAL
st.set_page_config(page_title="XRP 100 BOTS TERMINAL", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    [data-testid="stMetric"] { background-color: #FFFFFF !important; border-radius: 4px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 20px !important; font-weight: 900 !important; }
    .bot-line { border-bottom: 1px solid #222222; padding: 8px 0px; display: flex; justify-content: space-between; align-items: center; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 2px 6px; border-radius: 2px; font-weight: 900; }
    .stButton>button { width: 100%; border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION
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
    # ON REPASSE BIEN A 100 BOTS
    st.session_state.bots = mem.get("bots") if mem else {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE"} for i in range(100)}
    st.session_state.profit_total = mem.get("profit_total", 0.0) if mem else 0.0
    st.session_state.bankroll = 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ CMD 100 BOTS")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET (MIN 25$)", value=25.0)
    
    if st.button("🚨 RESET ALL DATA"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE"} for i in range(100)}
        sauvegarder(st.session_state.bots, 0.0); st.rerun()

    st.divider()
    # Zone défilante pour les 100 boutons de contrôle
    for i in range(100):
        id_b = f"B{i+1}"
        c1, c2 = st.columns([3, 1])
        if st.session_state.bots[id_b]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"g{i}"):
                if not kraken.markets: kraken.load_markets()
                pa_f, pv_f = float(kraken.price_to_precision('XRP/USDC', p_in)), float(kraken.price_to_precision('XRP/USDC', p_out))
                # Vérification Bankroll avant lancement
                if st.session_state.bankroll >= (b_val - 1):
                    vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                    try:
                        res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                        st.session_state.bots[id_b].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "oid": res['id'], "budget": b_val})
                        sauvegarder(st.session_state.bots, st.session_state.profit_total); st.rerun()
                    except Exception as e: st.error(f"Kraken: {e}")
                else:
                    st.warning("Solde insuffisant !")
        else:
            if c2.button("✖", key=f"o{i}"):
                st.session_state.bots[id_b]["status"] = "LIBRE"; st.rerun()

# --- MAIN LOOP ---
live = st.empty()
count = 0
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        if count % 5 == 0:
            st.session_state.bankroll = kraken.fetch_balance().get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET FEED : {px:.4f} XRP/USDC")
            c1, c2, c3 = st.columns(3)
            c1.metric("CASH DISPO", f"{st.session_state.bankroll:.2f} USDC")
            c2.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            c3.metric("BOTS ON", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            st.divider()
            
            # Affichage uniquement des bots actifs pour ne pas ralentir le PC
            actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
            if not actifs:
                st.info("Aucun bot en cours. Activez-en un dans la barre latérale.")
            
            for name in actifs:
                bot = st.session_state.bots[name]
                # Vérification auto si l'ordre est passé
                if bot["status"] == "ACHAT" and count % 2 == 0:
                    try:
                        info = kraken.fetch_order(bot["oid"])
                        if info['status'] == 'closed':
                            st.session_state.bots[name]["status"] = "VENTE"
                            vol = float(kraken.amount_to_precision('XRP/USDC', bot["budget"] / bot["pa"]))
                            v_res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["pv"])
                            st.session_state.bots[name]["oid"] = v_res['id']
                            sauvegarder(st.session_state.bots, st.session_state.profit_total)
                    except: pass

                sc = "#00FF00" if bot["status"] == "VENTE" else "#FFA500"
                st.markdown(f'<div class="bot-line"><b>{name}</b> <span style="color:{sc};">{bot["status"]}</span> <span>{bot["pa"]}->{bot["pv"]}</span> <span class="flash-box">{bot["budget"]:.2f} $</span></div>', unsafe_allow_html=True)
    except: pass
    count += 1
    time.sleep(10)
