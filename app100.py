import streamlit as st
import sys
import json
import os
import time
from datetime import datetime

# --- 1. SÉCURITÉ ---
try:
    import ccxt
except ImportError:
    st.error("Module CCXT manquant.")
    st.stop()

from streamlit_autorefresh import st_autorefresh
from config import get_kraken_connection

# --- 2. CONFIG & REFRESH ---
st.set_page_config(page_title="XRP AUTO-PILOT PRO", layout="wide")
st_autorefresh(interval=15000, key="datarefresh") 

if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

FILE_MEMOIRE = "etat_bots.json"
def sauvegarder(bots, total, histo, last_gain):
    with open(FILE_MEMOIRE, "w") as f: 
        json.dump({"bots": bots, "profit_total": total, "historique": histo, "last_gain": last_gain}, f)

def charger():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

# --- 3. INITIALISATION ---
if 'bots' not in st.session_state:
    mem = charger()
    if mem:
        st.session_state.bots = mem.get("bots")
        st.session_state.profit_total = mem.get("profit_total", 0.0)
        st.session_state.historique = mem.get("historique", [])
        st.session_state.last_gain_info = mem.get("last_gain", "Aucun gain")
    else:
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.session_state.profit_total = 0.0
        st.session_state.historique = []
        st.session_state.last_gain_info = "Aucun gain"

# --- 4. CONNEXION ---
kraken = None
try:
    kraken = get_kraken_connection()
except:
    st.sidebar.error("⚠️ API Kraken Error")

# --- 5. STYLE ---
profit_color = "#00FF00" if st.session_state.profit_total > 0 else "#0070FF"
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F2F6 !important; }}
    .status-dot {{ height: 10px; width: 10px; background-color: #00FF00; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #00FF00; animation: blinker 1.5s linear infinite; margin-right: 10px; }}
    @keyframes blinker {{ 50% {{ opacity: 0; }} }}
    [data-testid="stMetricValue"] {{ color: {profit_color} !important; font-size: 22px !important; font-weight: 900 !important; }}
    .bot-line {{ border-bottom: 1px solid #E6E9EF; padding: 8px 10px; display: flex; justify-content: space-between; align-items: center; background-color: #FFFFFF; margin-bottom: 2px; border-radius: 5px; font-size: 13px; }}
    .status-v {{ color: #28a745; font-weight: bold; }}
    .status-a {{ color: #fd7e14; font-weight: bold; }}
    .flash-box {{ background-color: #FFC107; color: black; padding: 2px 8px; border-radius: 4px; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. LOGIQUE LIVE & AUTO-RELANCE ---
px, cash_total = 0.0, 0.0
if kraken:
    try:
        if not kraken.markets: kraken.load_markets()
        ticker = kraken.fetch_ticker('XRP/USDC')
        px, bal = ticker['last'], kraken.fetch_balance()
        cash_total = bal.get('USDC', {}).get('total', 0.0)
        open_orders = kraken.fetch_open_orders('XRP/USDC')
        oids_kraken = [o['id'] for o in open_orders]

        for name, bot in st.session_state.bots.items():
            if bot["status"] != "LIBRE" and bot["oid"] != "NONE":
                if bot["oid"] not in oids_kraken:
                    try:
                        check = kraken.fetch_order(bot["oid"])
                        if check['status'] == 'closed':
                            old_status = bot["status"]
                            st.session_state.bots[name]["oid"] = "NONE" 
                            if old_status == "ACHAT":
                                vol_v = float(kraken.amount_to_precision('XRP/USDC', (bot["budget"] + bot.get("gain", 0)) / bot["pa"]))
                                v_res = kraken.create_limit_sell_order('XRP/USDC', vol_v, bot["pv"])
                                st.session_state.bots[name].update({"status": "VENTE", "oid": v_res['id']})
                            elif old_status == "VENTE":
                                profit = (float(bot["pv"]) - float(bot["pa"])) * (bot["budget"] / bot["pa"])
                                st.session_state.profit_total += profit
                                now_str = datetime.now().strftime("%H:%M:%S")
                                st.session_state.last_gain_info = f"+{profit:.4f}$ ({now_str})"
                                st.session_state.historique.insert(0, f"[{now_str}] {name}: +{profit:.4f}$")
                                st.session_state.historique = st.session_state.historique[:5]
                                pa_f = float(kraken.price_to_precision('XRP/USDC', bot["pa"]))
                                vol_a = float(kraken.amount_to_precision('XRP/USDC', (bot["budget"] + bot.get("gain", 0) + profit) / pa_f))
                                a_res = kraken.create_limit_buy_order('XRP/USDC', vol_a, pa_f, {'post-only': True})
                                st.session_state.bots[name].update({"status": "ACHAT", "oid": a_res['id'], "cycles": int(bot.get("cycles", 0)) + 1, "gain": float(bot.get("gain", 0)) + profit})
                            sauvegarder(st.session_state.bots, st.session_state.profit_total, st.session_state.historique, st.session_state.last_gain_info)
                            st.rerun()
                    except: pass
    except: st.caption("🔄 Synchro...")

# --- 7. AFFICHAGE TOP ---
uptime = int((time.time() - st.session_state.start_time) / 60)
st.markdown(f'<h3><span class="status-dot"></span>TERMINAL XRP LIVE <span style="font-size:12px; color:#888;">UPTIME: {uptime}m</span></h3>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("PRIX XRP", f"{px:.4f} $")
col2.metric("PROFIT TOTAL", f"+{st.session_state.profit_total:.4f} $")
col3.metric("DERNIER GAIN", st.session_state.last_gain_info)
col4.metric("WALLET TOTAL", f"{cash_total:.2f} $")
st.divider()

# --- 8. LANCEUR RAPIDE (NOUVEAU) ---
st.write("⚡ **LANCEUR ÉCLAIR**")
c_nb, c_in, c_out, c_go = st.columns([1,1,1,1])
nb_to_run = c_nb.number_input("Nombre de bots", min_value=1, max_value=100, value=5)
fast_in = c_in.number_input("IN", value=px if px > 0 else 1.4000, format="%.4f")
fast_out = c_out.number_input("OUT", value=(px*1.01) if px > 0 else 1.4100, format="%.4f")

if c_go.button("🚀 LANCER LA SÉRIE", use_container_width=True):
    count_launched = 0
    if kraken:
        for i in range(100):
            name = f"B{i+1}"
            if st.session_state.bots[name]["status"] == "LIBRE" and count_launched < nb_to_run:
                try:
                    if not kraken.markets: kraken.load_markets()
                    pa_f = float(kraken.price_to_precision('XRP/USDC', fast_in))
                    vol = float(kraken.amount_to_precision('XRP/USDC', 25.0 / pa_f))
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                    st.session_state.bots[name].update({"status": "ACHAT", "pa": pa_f, "pv": fast_out, "oid": res['id'], "budget": 25.0})
                    count_launched += 1
                except: continue
        sauvegarder(st.session_state.bots, st.session_state.profit_total, st.session_state.historique, st.session_state.last_gain_info)
        st.success(f"{count_launched} bots lancés d'un coup !")
        st.rerun()

st.divider()

# --- 9. LISTE DES BOTS ACTIFS ---
actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
for name in actifs:
    bot = st.session_state.bots[name]
    col_info, col_btn = st.columns([0.92, 0.08])
    with col_info:
        st.markdown(f'''
            <div class="bot-line">
                <b style="color:#2C3E50;">{name}</b>
                <span class="{"status-v" if bot["status"] == "VENTE" else "status-a"}">{bot["status"]}</span>
                <span>{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
                <span style="background:#EAECEE; padding:1px 6px; border-radius:3px; font-size:11px;">{bot.get("cycles",0)} CYC</span>
                <span class="flash-box">{bot["budget"] + bot.get("gain",0):.2f} $</span>
            </div>''', unsafe_allow_html=True)
    if col_btn.button("❌", key=f"del_{name}"):
        try:
            if bot["oid"] != "NONE": kraken.cancel_order(bot["oid"])
        except: pass
        st.session_state.bots[name].update({"status": "LIBRE", "oid": "NONE"})
        sauvegarder(st.session_state.bots, st.session_state.profit_total, st.session_state.historique, st.session_state.last_gain_info)
        st.rerun()
