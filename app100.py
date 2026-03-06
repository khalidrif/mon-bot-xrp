import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP BOT LIVE STATUS", layout="centered")

@st.cache_resource
def init_k():
    try:
        ex = ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
        })
        ex.nonce = lambda: ex.milliseconds()
        return ex
    except: return None

k = init_k()

# --- 2. MÉMOIRE ---
if 'bot' not in st.session_state:
    st.session_state.bot = {"status": "OFF", "pa": 1.40, "pv": 1.45, "cycles": 0, "profit": 0.0}

bot = st.session_state.bot

# --- 3. DASHBOARD LIVE ---
try:
    ticker = k.fetch_ticker('XRP/USDC')
    px = ticker['last']
    bal = k.fetch_balance()
    u_free = bal['free'].get('USDC', 0.0)
    x_free = bal['free'].get('XRP', 0.0)
    
    st.title("🏓 XRP Ping-Pong Live")
    
    # Métriques principales
    col1, col2, col3 = st.columns(3)
    col1.metric("PRIX XRP", f"{px:.4f}$")
    col2.metric("PROFIT", f"+{bot['profit']:.4f}$")
    col3.metric("CYCLES", bot["cycles"])

    # ÉTAT DU BOT (Le bandeau que tu as demandé)
    st.divider()
    orders = k.fetch_open_orders('XRP/USDC')
    
    if bot["status"] == "ON" and orders:
        o = orders[-1]
        if o['side'] == 'buy':
            st.warning(f"🟠 **ACHAT EN COURS** : {o['amount']} XRP à **{o['price']:.4f}$**")
            st.caption(f"Distance au prix actuel : {abs(px - o['price']):.4f}$")
        else:
            st.info(f"🔵 **VENTE EN COURS** : {o['amount']} XRP à **{o['price']:.4f}$**")
            st.caption(f"Distance au prix actuel : {abs(o['price'] - px):.4f}$")
    elif bot["status"] == "ON" and not orders:
        st.write("⏳ Synchronisation avec Kraken...")
    else:
        st.error("⚪ BOT À L'ARRÊT")

    st.divider()
    st.write(f"💰 Dispo: **{u_free:.2f} USDC** | 🪙 Dispo: **{x_free:.2f} XRP**")

except:
    st.error("Connexion Kraken interrompue.")
    st.stop()

# --- 4. RÉGLAGES ---
col_in, col_out = st.columns(2)
pa = col_in.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
pv = col_out.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")

# --- 5. BOUTONS ---
if bot["status"] == "OFF":
    if st.button("🚀 DÉMARRER LA BOUCLE", use_container_width=True, type="primary"):
        try:
            k.cancel_all_orders('XRP/USDC')
            bot.update({"status": "ON", "pa": pa, "pv": pv})
            st.rerun()
        except: pass
else:
    if st.button("🛑 ARRÊTER ET ANNULER", use_container_width=True):
        try: k.cancel_all_orders('XRP/USDC')
        except: pass
        bot["status"] = "OFF"
        st.rerun()

# --- 6. MOTEUR (FRAGMENT 15S) ---
if bot["status"] == "ON":
    @st.fragment(run_every=15)
    def engine():
        try:
            orders_live = k.fetch_open_orders('XRP/USDC')
            if not orders_live:
                bal_now = k.fetch_balance()
                u = bal_now['free'].get('USDC', 0.0)
                x = bal_now['free'].get('XRP', 0.0)
                
                if x > 5.0:
                    k.create_limit_sell_order('XRP/USDC', x, bot["pv"])
                elif u > 7.0:
                    vol = float(k.amount_to_precision('XRP/USDC', u / bot["pa"]))
                    k.create_limit_buy_order('XRP/USDC', vol, bot["pa"], {'post-only': True})
                st.rerun()
        except: pass
    engine()
