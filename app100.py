import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE BLOOMBERG ORIGINAL (100 LIGNES)
st.set_page_config(page_title="XRP 100 BOTS TERMINAL", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000 !important; color: #FFFFFF; font-family: 'Courier New', monospace; }
    .stApp { background-color: #000000 !important; }
    [data-testid="stMetric"] { background-color: #111111 !important; border: 1px solid #333; border-radius: 4px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 20px !important; }
    .bot-line { border-bottom: 1px solid #1a1a1a; padding: 6px 0px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; }
    .status-libre { color: #444; }
    .status-v { color: #00FF00; font-weight: bold; }
    .status-a { color: #FFA500; font-weight: bold; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 1px 6px; border-radius: 2px; font-weight: 900; }
    .bot-id { color: #888; width: 40px; }
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
    st.session_state.bots = mem.get("bots") if mem else {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
    st.session_state.profit_total = mem.get("profit_total", 0.0) if mem else 0.0
    st.session_state.bankroll = 0.0

# --- SIDEBAR (CONTRÔLE DES 100) ---
with st.sidebar:
    st.header("⚡ CMD 100 BOTS")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET (USDC)", value=25.0)
    
    if st.button("🚨 RESET ALL DATA"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        sauvegarder(st.session_state.bots, 0.0); st.rerun()

    st.write("---")
    # Liste défilante des boutons
    for i in range(100):
        name = f"B{i+1}"
        col1, col2 = st.columns([3, 1])
        if st.session_state.bots[name]["status"] == "LIBRE":
            if col1.button(f"RUN {i+1}", key=f"run{i}"):
                if st.session_state.bankroll >= 24.0:
                    try:
                        if not kraken.markets: kraken.load_markets()
                        pa_f, pv_f = float(kraken.price_to_precision('XRP/USDC', p_in)), float(kraken.price_to_precision('XRP/USDC', p_out))
                        vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                        res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                        st.session_state.bots[name].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "budget": b_val, "oid": res['id']})
                        sauvegarder(st.session_state.bots, st.session_state.profit_total); st.rerun()
                    except Exception as e: st.error("Erreur Kraken")
                else: st.warning("CASH INSUFFISANT")
        else:
            if col2.button("X", key=f"stop{i}"):
                st.session_state.bots[name]["status"] = "LIBRE"; st.rerun()

# --- MAIN LOOP ---
live = st.empty()
count = 0
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        if count % 5 == 0: st.session_state.bankroll = kraken.fetch_balance().get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET : {px:.4f} XRP/USDC")
            c1, c2, c3 = st.columns(3)
            c1.metric("CASH DISPO", f"{st.session_state.bankroll:.2f} $")
            c2.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            c3.metric("BOTS ON", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            st.divider()
            
            # AFFICHAGE DES 100 LIGNES
            for i in range(100):
                name = f"B{i+1}"
                bot = st.session_state.bots[name]
                
                # Logique de vérification auto (si actif)
                if bot["status"] == "ACHAT" and count % 2 == 0:
                    try:
                        if kraken.fetch_order(bot["oid"])['status'] == 'closed':
                            st.session_state.bots[name]["status"] = "VENTE"
                            vol = float(kraken.amount_to_precision('XRP/USDC', 25.0 / bot["pa"]))
                            v_res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["pv"])
                            st.session_state.bots[name]["oid"] = v_res['id']
                            sauvegarder(st.session_state.bots, st.session_state.profit_total)
                    except: pass

                # Style de la ligne selon le statut
                if bot["status"] == "LIBRE":
                    st.markdown(f'<div class="bot-line"><span class="bot-id">{name}</span><span class="status-libre">SYSTEM IDLE</span><span>---</span><span>0.00 $</span></div>', unsafe_allow_html=True)
                else:
                    label = "VENTE" if bot["status"] == "VENTE" else "ACHAT"
                    color = "status-v" if bot["status"] == "VENTE" else "status-a"
                    st.markdown(f'''<div class="bot-line"><span class="bot-id">{name}</span><span class="{color}">{label}</span><span>{bot["pa"]}->{bot["pv"]}</span><span class="flash-box">{bot["budget"]:.0f} $</span></div>''', unsafe_allow_html=True)

    except: pass
    count += 1
    time.sleep(10)
