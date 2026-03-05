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

# --- 2. CONFIG & REFRESH (15s) ---
st.set_page_config(page_title="XRP AUTO-PILOT PRO", layout="wide")
st_autorefresh(interval=15000, key="datarefresh") 

# COMPTEUR DE TEMPS (SESSION)
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

FILE_MEMOIRE = "etat_bots.json"
def sauvegarder(bots, total, histo):
    with open(FILE_MEMOIRE, "w") as f: 
        json.dump({"bots": bots, "profit_total": total, "historique": histo}, f)

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
        st.session_state.historique = mem.get("historique", [])
    else:
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.session_state.profit_total = 0.0
        st.session_state.historique = []

# --- 4. CONNEXION ---
kraken = None
try:
    kraken = get_kraken_connection()
except:
    st.sidebar.error("⚠️ API Kraken Error")

# --- 5. STYLE (PROFIT VERT FLASH) ---
profit_color = "#00FF00" if st.session_state.profit_total > 0 else "#0070FF"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F2F6 !important; }}
    .status-dot {{ height: 10px; width: 10px; background-color: #00FF00; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #00FF00; animation: blinker 1.5s linear infinite; margin-right: 10px; }}
    @keyframes blinker {{ 50% {{ opacity: 0; }} }}
    [data-testid="stMetricValue"] {{ color: {profit_color} !important; font-weight: 900 !important; }}
    .bot-line {{ border-bottom: 1px solid #E6E9EF; padding: 8px 10px; display: flex; justify-content: space-between; align-items: center; background-color: #FFFFFF; margin-bottom: 2px; border-radius: 5px; font-size: 13px; }}
    .status-v {{ color: #28a745; font-weight: bold; width: 60px; }}
    .status-a {{ color: #fd7e14; font-weight: bold; width: 60px; }}
    .flash-box {{ background-color: #FFC107; color: black; padding: 2px 8px; border-radius: 4px; font-weight: bold; }}
    .badge-cycle {{ background-color: #007bff; color: white; padding: 1px 8px; border-radius: 3px; font-size: 11px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.header("⚡ PILOTE AUTO")
    p_in = st.number_input("ACHAT (IN)", value=1.4000, format="%.4f")
    p_out = st.number_input("VENTE (OUT)", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET", value=25.0)
    bot_sel = st.selectbox("CHOISIR BOT", [f"B{i+1}" for i in range(100)])
    
    if st.button(f"🚀 ACTIVER {bot_sel}", use_container_width=True):
        if kraken:
            try:
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                st.session_state.bots[bot_sel].update({"status": "ACHAT", "pa": pa_f, "pv": p_out, "oid": res['id'], "budget": b_val})
                sauvegarder(st.session_state.bots, st.session_state.profit_total, st.session_state.historique)
                st.rerun()
            except Exception as e: st.error(f"Kraken: {e}")

# --- 7. LOGIQUE LIVE ---
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
                                st.session_state.historique.insert(0, f"[{datetime.now().strftime('%H:%M:%S')}] {name}: +{profit:.4f}$")
                                pa_f = float(kraken.price_to_precision('XRP/USDC', bot["pa"]))
                                vol_a = float(kraken.amount_to_precision('XRP/USDC', (bot["budget"] + bot.get("gain", 0) + profit) / pa_f))
                                a_res = kraken.create_limit_buy_order('XRP/USDC', vol_a, pa_f, {'post-only': True})
                                st.session_state.bots[name].update({"status": "ACHAT", "oid": a_res['id'], "cycles": int(bot.get("cycles", 0)) + 1, "gain": float(bot.get("gain", 0)) + profit})
                            sauvegarder(st.session_state.bots, st.session_state.profit_total, st.session_state.historique)
                            st.rerun()
                    except: pass
    except: st.caption("🔄 Synchro...")

# --- 8. AFFICHAGE ---
uptime = int((time.time() - st.session_state.start_time) / 60)
st.markdown(f'<h3><span class="status-dot"></span>TERMINAL XRP LIVE <span style="font-size:12px; color:#888;">UPTIME: {uptime}m</span></h3>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("PRIX XRP", f"{px:.4f} $")
c2.metric("NET PROFIT", f"+{st.session_state.profit_total:.4f} $")
c3.metric("WALLET TOTAL", f"{cash_total:.2f} $")
st.divider()

# Liste des bots actifs
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
                <span class="badge-cycle">{bot.get("cycles",0)} CYC</span>
                <span class="flash-box">{bot["budget"] + bot.get("gain",0):.2f} $</span>
            </div>''', unsafe_allow_html=True)
    if col_btn.button("❌", key=f"del_{name}"):
        try:
            if bot["oid"] != "NONE": kraken.cancel_order(bot["oid"])
        except: pass
        st.session_state.bots[name].update({"status": "LIBRE", "oid": "NONE"})
        sauvegarder(st.session_state.bots, st.session_state.profit_total, st.session_state.historique)
        st.rerun()

if st.session_state.historique:
    st.write("---")
    st.write("📊 **DERNIERS PROFITS**")
    for event in st.session_state.historique[:5]:
        st.markdown(f'<div class="histo-line">{event}</div>', unsafe_allow_html=True)
