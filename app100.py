import streamlit as st
import ccxt
import time
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP BOT MEMORY", layout="centered")

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

# --- 2. FONCTION DE COMPTAGE RÉEL (KRAKEN) ---
def count_real_cycles():
    try:
        # On récupère les 50 dernières transactions de vente sur XRP/USDC
        trades = k.fetch_my_trades('XRP/USDC', limit=50)
        # On compte combien de ventes (sell) ont été complétées
        ventes = [t for t in trades if t['side'] == 'sell']
        return len(ventes)
    except:
        return 0

# --- 3. MÉMOIRE DU BOT ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "pa": 1.40, "pv": 1.45, 
        "initial_balance": 71.35
    }

# --- 4. SYNC KRAKEN ---
def get_status():
    try:
        time.sleep(0.2)
        orders = k.fetch_open_orders('XRP/USDC')
        ticker = k.fetch_ticker('XRP/USDC')
        bal = k.fetch_balance()
        real_cycles = count_real_cycles()
        return orders, ticker['last'], bal, real_cycles
    except: return [], 1.40, None, 0

orders, px, bal, cycles = get_status()
u_free, x_free = 0.0, 0.0

st.title("🏓 XRP Ping-Pong")

if bal:
    u_free = bal['free'].get('USDC', 0.0)
    x_free = bal['free'].get('XRP', 0.0)
    
    # PROFIT RÉEL BASÉ SUR LE CAPITAL INITIAL
    valeur_actuelle = u_free + (x_free * px)
    profit_reel = valeur_actuelle - st.session_state.bot["initial_balance"]

    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX LIVE", f"{px:.4f}$")
    c2.metric("PROFIT NET", f"+{profit_reel:.4f}$")
    c3.metric("🔄 CYCLES", cycles) # AFFICHAGE DU COMPTEUR KRAKEN

    st.divider()
    
    if orders:
        o = orders[-1]
        type_ordre = "ACHAT" if o['side'] == 'buy' else "VENTE"
        couleur = "orange" if o['side'] == 'buy' else "blue"
        st.markdown(f"### <span style='color:{couleur}'>● {type_ordre} EN COURS</span>", unsafe_allow_html=True)
        st.info(f"**{o['amount']} XRP** à **{o['price']:.4f}$**")
        
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
        p_in = col_in.number_input("ACHAT (IN)", value=st.session_state.bot["pa"], format="%.4f")
        p_out = col_out.number_input("VENTE (OUT)", value=st.session_state.bot["pv"], format="%.4f")
        
        if st.button("🚀 LANCER LA BOUCLE", use_container_width=True, type="primary"):
            try:
                st.session_state.bot.update({"pa": p_in, "pv": p_out})
                if u_free > 7:
                    vol = float(k.amount_to_precision('XRP/USDC', u_free / p_in))
                    k.create_limit_buy_order('XRP/USDC', vol, p_in, {'post-only': True})
                elif x_free > 5:
                    k.create_limit_sell_order('XRP/USDC', x_free, p_out)
                st.rerun()
            except Exception as e: st.error(f"Erreur : {e}")

    st.divider()
    st.caption(f"💰 Portefeuille : {u_free:.2f} USDC | {x_free:.2f} XRP")

# --- 5. MOTEUR ---
if orders:
    @st.fragment(run_every=15)
    def engine():
        try:
            orders_live = k.fetch_open_orders('XRP/USDC')
            if not orders_live:
                # CYCLE RÉUSSI ! On laisse Kraken enregistrer le trade puis on relance
                time.sleep(2)
                bal_now = k.fetch_balance()
                u, x = bal_now['free'].get('USDC', 0.0), bal_now['free'].get('XRP', 0.0)
                p_in, p_out = st.session_state.bot["pa"], st.session_state.bot["pv"]
                
                if x > 5.0: 
                    k.create_limit_sell_order('XRP/USDC', x, p_out)
                elif u > 7.0:
                    vol = float(k.amount_to_precision('XRP/USDC', u / p_in))
                    k.create_limit_buy_order('XRP/USDC', vol, p_in, {'post-only': True})
                st.rerun()
        except: pass
    engine()
