import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP DYNAMIC BOT", layout="centered")

@st.cache_resource
def init_k():
    try:
        return ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True
        })
    except: return None

k = init_k()

# --- 2. MÉMOIRE ET SYNC ---
if 'bot' not in st.session_state:
    st.session_state.bot = {"status": "OFF", "pa": 1.40, "pv": 1.45, "oid": None, "cycles": 0, "profit": 0.0, "vol": 0.0}
    try:
        orders = k.fetch_open_orders('XRP/USDC')
        if orders:
            o = orders[-1]
            st.session_state.bot.update({"status": "ACHAT" if o['side']=='buy' else "VENTE", "oid": o['id'], "vol": o['amount'], "pv": o['price'] if o['side']=='sell' else 1.45})
    except: pass

bot = st.session_state.bot

# --- 3. DASHBOARD ---
ticker = k.fetch_ticker('XRP/USDC')
px = ticker['last']
bal = k.fetch_balance()

c1, c2 = st.columns(2)
c1.metric("🔥 XRP LIVE", f"{px:.4f}$")
c2.metric("🔄 CYCLES", bot["cycles"])

st.write(f"💰 {bal['free'].get('USDC', 0):.2f} USDC | 🪙 {bal['free'].get('XRP', 0):.2f} XRP")
st.divider()

# --- 4. MODIFICATION DU PRIX EN DIRECT ---
if bot["status"] != "OFF":
    st.subheader(f"🎯 CIBLE {bot['status']}")
    
    # Champ pour modifier le prix en direct
    new_pv = st.number_input("MODIFIER PRIX VENTE CIBLE", value=bot["pv"], format="%.4f")
    
    if bot["status"] == "VENTE" and new_pv != bot["pv"]:
        if st.button("✅ APPLIQUER NOUVEAU PRIX VENTE", use_container_width=True, type="primary"):
            try:
                k.cancel_order(bot["oid"]) # On annule l'ancien
                res = k.create_limit_sell_order('XRP/USDC', bot["vol"], new_pv) # On place le nouveau
                bot.update({"pv": new_pv, "oid": res['id']})
                st.success(f"Prix mis à jour : {new_pv}$")
                st.rerun()
            except Exception as e: st.error(f"Erreur MAJ: {e}")

    # Affichage distance
    target = bot["pa"] if bot["status"] == "ACHAT" else bot["pv"]
    st.info(f"Ordre actif à **{target:.4f}$** (Écart: {abs(target - px):.4f})")

    if st.button("🛑 STOP BOT", use_container_width=True):
        try: k.cancel_order(bot["oid"])
        except: pass
        bot["status"] = "OFF"
        st.rerun()
else:
    # REGLAGES START
    col_in, col_out = st.columns(2)
    pa_in = col_in.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
    pv_out = col_out.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")
    if st.button("🚀 START ALL-IN", use_container_width=True, type="primary"):
        u_free = bal['free'].get('USDC', 0)
        v = float(k.amount_to_precision('XRP/USDC', u_free / pa_in))
        res = k.create_limit_buy_order('XRP/USDC', v, pa_in, {'post-only': True})
        bot.update({"status": "ACHAT", "pa": pa_in, "pv": pv_out, "oid": res['id'], "vol": v})
        st.rerun()

# --- 5. ENGINE ---
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
                    bal_s = k.fetch_balance()
                    v_s = float(k.amount_to_precision('XRP/USDC', bal_s['free'].get('USDC', 0) / bot["pa"]))
                    res = k.create_limit_buy_order('XRP/USDC', v_s, bot["pa"], {'post-only': True})
                    bot.update({"status": "ACHAT", "oid": res['id'], "vol": v_s})
                st.rerun()
        except: pass
    engine()
