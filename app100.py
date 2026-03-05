import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP SMART-GRID", layout="centered")

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
        "cycles": 0, "profit": 0.0, "start_time": time.time()
    }

bot = st.session_state.bot

# --- 3. DASHBOARD ---
ticker = k.fetch_ticker('XRP/USDC')
px = ticker['last']
bal = k.fetch_balance()
u_free = bal['free'].get('USDC', 0.0)
x_free = bal['free'].get('XRP', 0.0)

# Gain par jour
jours = (time.time() - bot["start_time"]) / 86400
gain_j = bot["profit"] / jours if jours > 0.001 else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("🔥 XRP", f"{px:.4f}$")
c2.metric("🔄 CYCLES", bot["cycles"])
c3.metric("📅 / JOUR", f"{gain_j:.2f}$")
st.metric("📈 NET PROFIT TOTAL", f"+{bot['profit']:.4f} $")
st.write(f"💰 {u_free:.2f} USDC | 🪙 {x_free:.2f} XRP")
st.divider()

# --- 4. FONCTION SÉCURISÉE POUR PLACER ORDRES ---
def safe_place_buy(amount_usdc, price):
    if amount_usdc < 5.0: return None # Minimum ~5 USDC
    vol = float(k.amount_to_precision('XRP/USDC', amount_usdc / price))
    if vol < 5.0: return None # Minimum Kraken ~5 XRP
    res = k.create_limit_buy_order('XRP/USDC', vol, price, {'post-only': True})
    return res['id']

def safe_place_sell(amount_xrp, price):
    if amount_xrp < 5.0: return None # Minimum Kraken ~5 XRP
    res = k.create_limit_sell_order('XRP/USDC', amount_xrp, price)
    return res['id']

# --- 5. AJUSTEMENT ---
st.subheader("⚙️ Ajuster la fourchette")
col_in, col_out = st.columns(2)
new_pa = col_in.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
new_pv = col_out.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")

if bot["status"] == "ON":
    if new_pa != bot["pa"] or new_pv != bot["pv"]:
        if st.button("🔄 APPLIQUER LES NOUVEAUX PRIX", use_container_width=True):
            try:
                # Update ACHAT
                if bot["oid_buy"]:
                    try: k.cancel_order(bot["oid_buy"])
                    except: pass
                bot["oid_buy"] = safe_place_buy(u_free, new_pa)
                
                # Update VENTE
                if bot["oid_sell"]:
                    try: k.cancel_order(bot["oid_sell"])
                    except: pass
                bot["oid_sell"] = safe_place_sell(x_free, new_pv)
                
                bot["pa"], bot["pv"] = new_pa, new_pv
                st.toast("✅ Prix mis à jour !")
                st.rerun()
            except Exception as e: st.error(f"Erreur : {e}")

# --- 6. START / STOP ---
if bot["status"] == "OFF":
    if st.button("🚀 DÉMARRER LE BOT", use_container_width=True, type="primary"):
        bot.update({"status": "ON", "pa": new_pa, "pv": new_pv})
        try:
            bot["oid_buy"] = safe_place_buy(u_free, new_pa)
            bot["oid_sell"] = safe_place_sell(x_free, new_pv)
            st.rerun()
        except Exception as e: st.error(f"Erreur Start : {e}")
else:
    if st.button("🛑 ARRÊTER ET ANNULER", use_container_width=True):
        try:
            if bot["oid_buy"]: k.cancel_order(bot["oid_buy"])
        except: pass
        try:
            if bot["oid_sell"]: k.cancel_order(bot["oid_sell"])
        except: pass
        bot.update({"status": "OFF", "oid_buy": None, "oid_sell": None})
        st.rerun()

# --- 7. MOTEUR ---
if bot["status"] == "ON":
    @st.fragment(run_every=15)
    def engine():
        try:
            if bot["oid_buy"]:
                o_b = k.fetch_order(bot["oid_buy"], 'XRP/USDC')
                if o_b['status'] == 'closed':
                    try: k.cancel_order(bot["oid_sell"])
                    except: pass
                    bal_n = k.fetch_balance()
                    bot["oid_sell"] = safe_place_sell(bal_n['free'].get('XRP', 0), bot["pv"])
                    bot["oid_buy"] = None
                    st.rerun()

            if bot["oid_sell"]:
                o_s = k.fetch_order(bot["oid_sell"], 'XRP/USDC')
                if o_s['status'] == 'closed':
                    bot["profit"] += (bot["pv"] - bot["pa"]) * o_s['filled']
                    bot["cycles"] += 1
                    try: k.cancel_order(bot["oid_buy"])
                    except: pass
                    bal_n = k.fetch_balance()
                    bot["oid_buy"] = safe_place_buy(bal_n['free'].get('USDC', 0), bot["pa"])
                    bot["oid_sell"] = None
                    st.rerun()
        except: pass
    engine()
