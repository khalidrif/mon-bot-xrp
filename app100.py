import streamlit as st
import ccxt
import time
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="XRP MINI", layout="centered")

@st.cache_resource
def init_k():
    return ccxt.kraken({'apiKey': st.secrets["KRAKEN_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})

k = init_k()

if 'bot' not in st.session_state:
    st.session_state.bot = {"status": "OFF", "pa": 1.40, "pv": 1.45, "oid": None, "cycles": 0, "profit": 0.0, "vol": 0.0}
    try:
        orders = k.fetch_open_orders('XRP/USDC')
        if orders:
            o = orders[-1]
            st.session_state.bot.update({"status": "ACHAT" if o['side']=='buy' else "VENTE", "oid": o['id'], "vol": o['amount']})
    except: pass

# --- UI COMPACTE ---
bot = st.session_state.bot
ticker = k.fetch_ticker('XRP/USDC')
px = ticker['last']

c1, c2 = st.columns(2)
c1.metric("LIVE", f"{px:.4f}$")
c2.metric("PROFIT", f"+{bot['profit']:.4f}$")

if bot["status"] != "OFF":
    target = bot["pa"] if bot["status"] == "ACHAT" else bot["pv"]
    diff = abs(target - px)
    st.info(f"🎯 **{bot['status']}** à **{target:.4f}$** (Reste {diff:.4f})")
    
    if st.button("🛑 STOP", use_container_width=True):
        try: k.cancel_order(bot["oid"])
        except: pass
        bot["status"] = "OFF"
        st.rerun()
else:
    col_a, col_v = st.columns(2)
    pa = col_a.number_input("IN", value=bot["pa"], format="%.4f")
    pv = col_v.number_input("OUT", value=bot["pv"], format="%.4f")
    if st.button("🚀 START", use_container_width=True, type="primary"):
        bal = k.fetch_balance()
        v = float(k.amount_to_precision('XRP/USDC', bal['free'].get('USDC', 0) / pa))
        res = k.create_limit_buy_order('XRP/USDC', v, pa, {'post-only': True})
        bot.update({"status": "ACHAT", "pa": pa, "pv": pv, "oid": res['id'], "vol": v})
        st.rerun()

st.caption(f"Cycles: {bot['cycles']} | {datetime.now().strftime('%H:%M:%S')}")

# --- ENGINE ---
if bot["status"] != "OFF":
    @st.fragment(run_every=15)
    def engine():
        try:
            o = k.fetch_order(bot["oid"], 'XRP/USDC')
            if o['status'] == 'closed':
                if bot["status"] == "ACHAT":
                    res = k.create_limit_sell_order('XRP/USDC', o['filled'], bot["pv"])
                    bot.update({"status": "VENTE", "oid": res['id'], "vol": o['filled']})
                else:
                    bot["profit"] += (bot["pv"] - bot["pa"]) * o['filled']
                    bot["cycles"] += 1
                    bal = k.fetch_balance()
                    v = float(k.amount_to_precision('XRP/USDC', bal['free'].get('USDC', 0) / bot["pa"]))
                    res = k.create_limit_buy_order('XRP/USDC', v, bot["pa"], {'post-only': True})
                    bot.update({"status": "ACHAT", "oid": res['id'], "vol": v})
                st.rerun()
        except: pass
    engine()
