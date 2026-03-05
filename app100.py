import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP DOUBLE-PROFIT", layout="centered")

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

# --- 2. MÉMOIRE ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", "pa": 1.40, "pv": 1.45, 
        "oid_buy": None, "oid_sell": None, 
        "cycles": 0, "profit": 0.0, "start_time": None
    }

bot = st.session_state.bot

# --- 3. DASHBOARD ET MÉTRIQUES ---
def draw_metrics():
    try:
        ticker = k.fetch_ticker('XRP/USDC')
        px = ticker['last']
        bal = k.fetch_balance()
        u_free = bal['free'].get('USDC', 0.0)
        x_free = bal['free'].get('XRP', 0.0)

        # Calcul Profit par jour
        profit_total = bot["profit"]
        gain_jour = 0.0
        if bot["start_time"]:
            jours = (time.time() - bot["start_time"]) / 86400
            gain_jour = profit_total / jours if jours > 0.001 else 0.0

        # Affichage
        c1, c2, c3 = st.columns(3)
        c1.metric("🔥 XRP LIVE", f"{px:.4f}$")
        c2.metric("🔄 CYCLES", bot["cycles"])
        c3.metric("📅 GAIN / JOUR", f"{gain_jour:.2f}$")

        st.metric("📈 NET PROFIT TOTAL", f"+{profit_total:.4f} $")
        
        st.write(f"💰 **{u_free:.2f} USDC** | 🪙 **{x_free:.2f} XRP**")
        st.divider()
        return px, u_free, x_free
    except: 
        st.warning("Connexion Kraken...")
        return 1.40, 0, 0

px_live, usdc, xrp = draw_metrics()

# --- 4. CONTRÔLE ---
if bot["status"] == "ON":
    st.success(f"🎯 DOUBLE-ACTION ACTIF (In: {bot['pa']} | Out: {bot['pv']})")
    if st.button("🛑 TOUT ARRÊTER ET ANNULER", use_container_width=True, type="primary"):
        try:
            if bot["oid_buy"]: k.cancel_order(bot["oid_buy"])
            if bot["oid_sell"]: k.cancel_order(bot["oid_sell"])
        except: pass
        bot.update({"status": "OFF", "oid_buy": None, "oid_sell": None})
        st.rerun()
else:
    col_in, col_out = st.columns(2)
    pa_in = col_in.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
    pv_out = col_out.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")

    if st.button("🚀 LANCER LES DEUX ORDRES", use_container_width=True, type="primary"):
        try:
            if not bot["start_time"]: bot["start_time"] = time.time()
            oid_b, oid_s = None, None
            if usdc > 5:
                v_b = float(k.amount_to_precision('XRP/USDC', usdc / pa_in))
                res_b = k.create_limit_buy_order('XRP/USDC', v_b, pa_in, {'post-only': True})
                oid_b = res_b['id']
            if xrp > 1:
                res_s = k.create_limit_sell_order('XRP/USDC', xrp, pv_out)
                oid_s = res_s['id']
            bot.update({"status": "ON", "pa": pa_in, "pv": pv_out, "oid_buy": oid_b, "oid_sell": oid_s})
            st.rerun()
        except Exception as e: st.error(f"Erreur: {e}")

# --- 5. MOTEUR (15S) ---
if bot["status"] == "ON":
    @st.fragment(run_every=15)
    def engine():
        try:
            # Check ACHAT
            if bot["oid_buy"]:
                o_b = k.fetch_order(bot["oid_buy"], 'XRP/USDC')
                if o_b['status'] == 'closed':
                    try: k.cancel_order(bot["oid_sell"])
                    except: pass
                    bal_n = k.fetch_balance()
                    res_s = k.create_limit_sell_order('XRP/USDC', bal_n['free'].get('XRP', 0), bot["pv"])
                    bot.update({"oid_buy": None, "oid_sell": res_s['id']})
                    st.rerun()

            # Check VENTE
            if bot["oid_sell"]:
                o_s = k.fetch_order(bot["oid_sell"], 'XRP/USDC')
                if o_s['status'] == 'closed':
                    bot["profit"] += (bot["pv"] - bot["pa"]) * o_s['filled']
                    bot["cycles"] += 1
                    try: k.cancel_order(bot["oid_buy"])
                    except: pass
                    bal_n = k.fetch_balance()
                    v_new = float(k.amount_to_precision('XRP/USDC', bal_n['free'].get('USDC', 0) / bot["pa"]))
                    res_b = k.create_limit_buy_order('XRP/USDC', v_new, bot["pa"], {'post-only': True})
                    bot.update({"oid_buy": res_b['id'], "oid_sell": None})
                    st.rerun()
        except: pass
    engine()
