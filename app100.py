import streamlit as st
import ccxt
import time
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP BOT PROFIT+", layout="centered")

@st.cache_resource
def init_k():
    try:
        exchange = ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
        })
        exchange.nonce = lambda: exchange.milliseconds()
        return exchange
    except: return None

k = init_k()

def play_notification_sound():
    sound_url = "https://www.soundjay.com"
    components.html(f'<audio autoplay><source src="{sound_url}" type="audio/mpeg"></audio>', height=0)

# --- 2. MÉMOIRE PERSISTANTE ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "pa": 1.40, "pv": 1.45, 
        "cycles": 0, "profit": 0.0, 
        "initial_balance": 71.35  # Ton capital de départ
    }

# --- 3. SYNC KRAKEN ---
def get_status():
    try:
        time.sleep(0.2)
        orders = k.fetch_open_orders('XRP/USDC')
        ticker = k.fetch_ticker('XRP/USDC')
        bal = k.fetch_balance()
        return orders, ticker['last'], bal
    except: return [], 1.40, None

orders, px, bal = get_status()
u_free, x_free = 0.0, 0.0

st.title("🏓 XRP Ping-Pong")

if bal:
    u_free = bal['free'].get('USDC', 0.0)
    x_free = bal['free'].get('XRP', 0.0)
    
    # CALCUL DU PROFIT RÉEL (Basé sur ton capital de départ)
    # Valeur actuelle = USDC libre + (XRP * Prix actuel)
    current_value = u_free + (x_free * px)
    st.session_state.bot["profit"] = current_value - st.session_state.bot["initial_balance"]

    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX LIVE", f"{px:.4f}$")
    c2.metric("PROFIT NET", f"+{st.session_state.bot['profit']:.4f}$")
    c3.metric("🔄 CYCLES", st.session_state.bot["cycles"])

    st.divider()
    
    if orders:
        o = orders[-1]
        if o['side'] == 'buy':
            st.warning(f"🟠 **ACHAT EN COURS** : {o['amount']} XRP à **{o['price']:.4f}$**")
        else:
            st.info(f"🔵 **VENTE EN COURS** : {o['amount']} XRP à **{o['price']:.4f}$**")
        
        if st.button("🛑 ARRÊTER ET TOUT ANNULER", use_container_width=True, type="primary"):
            try:
                k.cancel_all_orders('XRP/USDC')
                st.rerun()
            except: pass
    else:
        st.error("⚪ BOT À L'ARRÊT")
        st.divider()
        st.subheader("⚙️ Configuration")
        col_in, col_out = st.columns(2)
        
        st.session_state.bot["pa"] = col_in.number_input("ACHAT (IN)", value=st.session_state.bot["pa"], format="%.4f")
        st.session_state.bot["pv"] = col_out.number_input("VENTE (OUT)", value=st.session_state.bot["pv"], format="%.4f")
        
        if st.button("🚀 LANCER LA BOUCLE", use_container_width=True, type="primary"):
            try:
                p_in, p_out = st.session_state.bot["pa"], st.session_state.bot["pv"]
                if u_free > 7:
                    vol = float(k.amount_to_precision('XRP/USDC', u_free / p_in))
                    k.create_limit_buy_order('XRP/USDC', vol, p_in, {'post-only': True})
                elif x_free > 5:
                    k.create_limit_sell_order('XRP/USDC', x_free, p_out)
                st.rerun()
            except Exception as e: st.error(f"Erreur : {e}")

    st.divider()
    st.write(f"💰 USDC: **{u_free:.2f}** | 🪙 XRP: **{x_free:.2f}**")

# --- 4. MOTEUR ---
if orders:
    @st.fragment(run_every=15)
    def engine():
        try:
            orders_live = k.fetch_open_orders('XRP/USDC')
            if not orders_live:
                play_notification_sound()
                st.balloons()
                
                # Incrémenter le cycle uniquement après une vente réussie
                bal_now = k.fetch_balance()
                u, x = bal_now['free'].get('USDC', 0.0), bal_now['free'].get('XRP', 0.0)
                p_in, p_out = st.session_state.bot["pa"], st.session_state.bot["pv"]
                
                if x > 5.0: # On vient d'acheter
                    k.create_limit_sell_order('XRP/USDC', x, p_out)
                elif u > 7.0: # On vient de vendre
                    st.session_state.bot["cycles"] += 1
                    vol = float(k.amount_to_precision('XRP/USDC', u / p_in))
                    k.create_limit_buy_order('XRP/USDC', vol, p_in, {'post-only': True})
                st.rerun()
        except: pass
    engine()
