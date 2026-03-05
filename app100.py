import streamlit as st
import sys
import json
import os

# --- PATCH DE SÉCURITÉ ---
try:
    import ccxt
except ImportError:
    st.stop()

from streamlit_autorefresh import st_autorefresh
from config import get_kraken_connection

# 1. CONFIG & REFRESH 15s
st.set_page_config(page_title="XRP Terminal Pro", layout="wide")
st_autorefresh(interval=15000, key="datarefresh") 

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
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.session_state.profit_total = 0.0

# 2. CONNEXION KRAKEN
kraken = get_kraken_connection()

# --- SIDEBAR CMD ---
with st.sidebar:
    st.header("⚙️ CONFIGURATION")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET (USDC)", value=25.0)
    bot_sel = st.selectbox("SÉLECTIONNER BOT", [f"B{i+1}" for i in range(100)])
    
    if st.button(f"🚀 GO {bot_sel}", use_container_width=True):
        if kraken:
            try:
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                st.session_state.bots[bot_sel].update({"status": "ACHAT", "pa": pa_f, "pv": p_out, "oid": res['id'], "budget": b_val})
                sauvegarder(st.session_state.bots, st.session_state.profit_total)
                st.rerun()
            except Exception as e: st.error(f"Kraken: {e}")

# --- LOGIQUE DE VÉRIFICATION RÉELLE KRAKEN ---
try:
    if not kraken.markets: kraken.load_markets()
    ticker = kraken.fetch_ticker('XRP/USDC')
    px = ticker['last']
    bal = kraken.fetch_balance()
    cash = bal.get('USDC', {}).get('free', 0.0)

    # BOUCLE DE SURVEILLANCE DES ORDRES
    for name, bot in st.session_state.bots.items():
        if bot["status"] != "LIBRE" and bot["oid"] != "NONE":
            try:
                order = kraken.fetch_order(bot["oid"])
                # SI L'ACHAT EST FINI -> ON PLACE LA VENTE
                if order['status'] == 'closed' and bot["status"] == "ACHAT":
                    vol_v = float(kraken.amount_to_precision('XRP/USDC', (bot["budget"]+bot["gain"])/bot["pa"]))
                    pv_f = float(kraken.price_to_precision('XRP/USDC', bot["pv"]))
                    v_res = kraken.create_limit_sell_order('XRP/USDC', vol_v, pv_f)
                    st.session_state.bots[name].update({"status": "VENTE", "oid": v_res['id']})
                    sauvegarder(st.session_state.bots, st.session_state.profit_total)
                
                # SI LA VENTE EST FINIE -> CYCLE SUIVANT
                elif order['status'] == 'closed' and bot["status"] == "VENTE":
                    profit = (bot["pv"] - bot["pa"]) * (bot["budget"]/bot["pa"])
                    st.session_state.profit_total += profit
                    st.session_state.bots[name].update({"status": "LIBRE", "oid": "NONE", "cycles": bot["cycles"]+1, "gain": bot["gain"]+profit})
                    sauvegarder(st.session_state.bots, st.session_state.profit_total)
            except: pass

    # --- AFFICHAGE ---
    st.markdown(f'<h3><span class="status-dot"></span>TERMINAL XRP LIVE</h3>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX XRP", f"{px:.4f} $")
    c2.metric("GAIN TOTAL", f"+{st.session_state.profit_total:.4f} $")
    c3.metric("CASH DISPO", f"{cash:.2f} $")
    st.divider()

    actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
    for name in actifs:
        bot = st.session_state.bots[name]
        st.markdown(f'''
            <div class="bot-line">
                <b style="color:#2C3E50;">{name}</b>
                <span class="{"status-v" if bot["status"] == "VENTE" else "status-a"}">{bot["status"]}</span>
                <span>{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
                <span class="badge-cycle">{bot["cycles"]} CYCLES</span>
                <span class="flash-box">{bot["budget"] + bot["gain"]:.2f} $</span>
            </div>''', unsafe_allow_html=True)
except Exception as e: st.info("Chargement...")
