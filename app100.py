import streamlit as st
import ccxt
import time
import streamlit.components.v1 as components

# --- 1. CONFIGURATION STABLE ---
st.set_page_config(page_title="XRP BOT STABLE", layout="centered")

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

# --- SONORE ---
def play_notification_sound():
    sound_url = "https://www.soundjay.com"
    components.html(f'<audio autoplay><source src="{sound_url}" type="audio/mpeg"></audio>', height=0)

# --- 2. MÉMOIRE DU BOT ---
if 'bot' not in st.session_state:
    st.session_state.bot = {"status": "OFF", "pa": 1.40, "pv": 1.45, "cycles": 0, "profit": 0.0}

bot = st.session_state.bot

# --- 3. SYNC KRAKEN ---
def get_kraken_status():
    try:
        time.sleep(0.2)
        open_orders = k.fetch_open_orders('XRP/USDC')
        ticker = k.fetch_ticker('XRP/USDC')
        bal = k.fetch_balance()
        return open_orders, ticker['last'], bal
    except: return [], 1.40, None

orders, px, bal = get_kraken_status()

# Initialisation des variables de solde
u_free, x_free = 0.0, 0.0

# --- 4. DASHBOARD ---
st.title("🏓 XRP Ping-Pong Stable")

if bal:
    u_free = bal['free'].get('USDC', 0.0)
    x_free = bal['free'].get('XRP', 0.0)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX LIVE", f"{px:.4f}$")
    c2.metric("PROFIT", f"+{bot['profit']:.4f}$")
    c3.metric("🔄 CYCLES", bot["cycles"])

    st.divider()
    
    # AFFICHAGE DU STATUT RÉEL
    if orders:
        o = orders[-1]
        if o['side'] == 'buy':
            st.warning(f"🟠 **ACHAT EN COURS** : {o['amount']} XRP à **{o['price']:.4f}$**")
        else:
            st.info(f"🔵 **VENTE EN COURS** : {o['amount']} XRP à **{o['price']:.4f}$**")
    else:
        st.error("⚪ BOT À L'ARRÊT (AUCUN ORDRE)")
    
    st.write(f"💰 Dispo: **{u_free:.2f} USDC** | 🪙 Dispo: **{x_free:.2f} XRP**")

st.divider()

# --- 5. RÉGLAGES (ACTIFS UNIQUEMENT SI LE BOT EST ARRÊTÉ) ---
if not orders:
    st.subheader("⚙️ Réglages du prochain cycle")
    col_in, col_out = st.columns(2)
    pa = col_in.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
    pv = col_out.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")
    
    if st.button("🚀 LANCER LA BOUCLE", use_container_width=True, type="primary"):
        try:
            bot.update({"status": "ON", "pa": pa, "pv": pv})
            if u_free > 7:
                vol = float(k.amount_to_precision('XRP/USDC', u_free / pa))
                k.create_limit_buy_order('XRP/USDC', vol, pa, {'post-only': True})
            elif x_free > 5:
                k.create_limit_sell_order('XRP/USDC', x_free, pv)
            st.rerun()
        except Exception as e: st.error(f"Erreur : {e}")
else:
    # SI LE BOT TOURNE, ON AFFICHE UNIQUEMENT LE BOUTON ARRÊT
    st.write("Pour modifier les prix, arrêtez d'abord le bot.")
    if st.button("🛑 ARRÊTER ET TOUT ANNULER", use_container_width=True, type="primary"):
        try:
            k.cancel_all_orders('XRP/USDC')
            bot["status"] = "OFF"
            st.rerun()
        except: pass

# --- 6. MOTEUR DE SURVEILLANCE ---
if orders: # Le moteur ne tourne que s'il y a un ordre à surveiller
    @st.fragment(run_every=15)
    def engine():
        try:
            orders_live = k.fetch_open_orders('XRP/USDC')
            if not orders_live:
                # CYCLE RÉUSSI !
                play_notification_sound()
                st.balloons()
                
                # Récupération des infos pour le prochain tour
                bal_now = k.fetch_balance()
                u = bal_now['free'].get('USDC', 0.0)
                x = bal_now['free'].get('XRP', 0.0)
                
                if x > 5.0: # On vient d'acheter -> On vend
                    k.create_limit_sell_order('XRP/USDC', x, bot["pv"])
                elif u > 7.0: # On vient de vendre -> On rachète (Achat = Profit inclus)
                    bot["profit"] += (bot["pv"] - bot["pa"]) * (u / bot["pv"]) # Estimé
                    bot["cycles"] += 1
                    vol = float(k.amount_to_precision('XRP/USDC', u / bot["pa"]))
                    k.create_limit_buy_order('XRP/USDC', vol, bot["pa"], {'post-only': True})
                st.rerun()
        except: pass
    engine()
