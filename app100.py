import streamlit as st
import ccxt
import time
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP BOT SONORE", layout="centered")

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

# --- FONCTION SONORE (HTML/JS) ---
def play_notification_sound():
    # Un son court et propre pour la validation de transaction
    sound_url = "https://www.soundjay.com"
    components.html(
        f"""
        <audio autoplay>
            <source src="{sound_url}" type="audio/mpeg">
        </audio>
        """,
        height=0,
    )

# --- 2. MÉMOIRE DU BOT ---
if 'bot' not in st.session_state:
    st.session_state.bot = {"status": "OFF", "pa": 1.40, "pv": 1.45, "cycles": 0, "profit": 0.0}

bot = st.session_state.bot

# --- 3. SYNC KRAKEN ---
def get_kraken_status():
    try:
        open_orders = k.fetch_open_orders('XRP/USDC')
        ticker = k.fetch_ticker('XRP/USDC')
        bal = k.fetch_balance()
        return open_orders, ticker['last'], bal
    except: return [], 1.40, None

orders, px, bal = get_kraken_status()

# --- 4. DASHBOARD ---
st.title("🏓 XRP Ping-Pong Audio")

if bal:
    u_free = bal['free'].get('USDC', 0.0)
    x_free = bal['free'].get('XRP', 0.0)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX LIVE", f"{px:.4f}$")
    c2.metric("PROFIT", f"+{bot['profit']:.4f}$")
    c3.metric("🔄 CYCLES", bot["cycles"])

    st.divider()
    if orders:
        o = orders[-1]
        bot["status"] = "ON"
        if o['side'] == 'buy':
            st.warning(f"🟠 **ACHAT EN COURS** : {o['amount']} XRP à **{o['price']:.4f}$**")
        else:
            st.info(f"🔵 **VENTE EN COURS** : {o['amount']} XRP à **{o['price']:.4f}$**")
    else:
        st.error("⚪ AUCUN ORDRE ACTIF")
    
    st.divider()
    st.write(f"💰 Dispo: **{u_free:.2f} USDC** | 🪙 Dispo: **{x_free:.2f} XRP**")

# --- 5. RÉGLAGES ---
col_in, col_out = st.columns(2)
pa = col_in.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
pv = col_out.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")

# --- 6. BOUTONS ---
if not orders:
    if st.button("🚀 LANCER LA BOUCLE", use_container_width=True, type="primary"):
        try:
            bot.update({"status": "ON", "pa": pa, "pv": pv})
            if u_free > 7:
                vol = float(k.amount_to_precision('XRP/USDC', u_free / pa))
                k.create_limit_buy_order('XRP/USDC', vol, pa, {'post-only': True})
            elif x_free > 5:
                k.create_limit_sell_order('XRP/USDC', x_free, pv)
            st.rerun()
        except Exception as e: st.error(e)
else:
    if st.button("🛑 ARRÊTER ET ANNULER", use_container_width=True):
        try: k.cancel_all_orders('XRP/USDC')
        except: pass
        bot["status"] = "OFF"
        st.rerun()

# --- 7. MOTEUR ---
if bot["status"] == "ON":
    @st.fragment(run_every=15)
    def engine():
        try:
            orders_live = k.fetch_open_orders('XRP/USDC')
            if not orders_live:
                # UN ORDRE VIENT D'ÊTRE REMPLI !
                play_notification_sound() # <--- JOUE LE SON ICI
                st.balloons() # <--- EFFET VISUEL
                
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
