import streamlit as st
import ccxt
import time
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ANTI-NONCE ---
st.set_page_config(page_title="XRP BOT ULTRA-SHIELD", layout="centered")

@st.cache_resource
def init_k():
    try:
        exchange = ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
        })
        # FIX DEFINITIF POUR L'ERREUR NONCE
        exchange.nonce = lambda: exchange.milliseconds()
        return exchange
    except: return None

k = init_k()

# --- SONORE ---
def play_notification_sound():
    sound_url = "https://www.soundjay.com"
    components.html(f'<audio autoplay><source src="{sound_url}" type="audio/mpeg"></audio>', height=0)

# --- 2. MÉMOIRE ---
if 'bot' not in st.session_state:
    st.session_state.bot = {"status": "OFF", "pa": 1.40, "pv": 1.45, "cycles": 0, "profit": 0.0}

bot = st.session_state.bot

# --- 3. SYNC KRAKEN (SÉCURISÉE) ---
def get_kraken_status():
    try:
        # Petite pause pour éviter le spam API
        time.sleep(0.2)
        open_orders = k.fetch_open_orders('XRP/USDC')
        ticker = k.fetch_ticker('XRP/USDC')
        bal = k.fetch_balance()
        return open_orders, ticker['last'], bal
    except: return [], 1.40, None

orders, px, bal = get_kraken_status()

# --- 4. DASHBOARD ---
st.title("🛡️ XRP Bot Ultra-Shield")

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
    
    st.write(f"💰 Dispo: **{u_free:.2f} USDC** | 🪙 Dispo: **{x_free:.2f} XRP**")

st.divider()

# --- 5. RÉGLAGES ---
st.subheader("⚙️ Ajuster les prix")
col_in, col_out = st.columns(2)
new_pa = col_in.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
new_pv = col_out.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")

# --- 6. LOGIQUE DE MODIFICATION (SÉCURISÉE ANTI-NONCE) ---
if orders and (new_pa != bot["pa"] or new_pv != bot["pv"]):
    if st.button("🔄 APPLIQUER LES NOUVEAUX PRIX", use_container_width=True, type="primary"):
        try:
            # Étape 1 : Annuler tout
            k.cancel_all_orders('XRP/USDC')
            st.toast("Annulation en cours...")
            
            # Étape 2 : Pause forcée de 2 secondes pour laisser Kraken respirer
            time.sleep(2) 
            
            # Étape 3 : Ré-interroger le solde après annulation
            new_bal = k.fetch_balance()
            u, x = new_bal['free'].get('USDC', 0.0), new_bal['free'].get('XRP', 0.0)
            
            # Étape 4 : Placer le nouvel ordre
            if x > 5:
                k.create_limit_sell_order('XRP/USDC', x, new_pv)
            elif u > 7:
                vol = float(k.amount_to_precision('XRP/USDC', u / new_pa))
                k.create_limit_buy_order('XRP/USDC', vol, new_pa, {'post-only': True})
            
            bot.update({"pa": new_pa, "pv": new_pv})
            st.success("✅ Mise à jour réussie !")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

# --- 7. START / STOP ---
if not orders:
    if st.button("🚀 LANCER LA BOUCLE", use_container_width=True, type="primary"):
        try:
            bot.update({"status": "ON", "pa": new_pa, "pv": new_pv})
            if u_free > 7:
                vol = float(k.amount_to_precision('XRP/USDC', u_free / new_pa))
                k.create_limit_buy_order('XRP/USDC', vol, new_pa, {'post-only': True})
            elif x_free > 5:
                k.create_limit_sell_order('XRP/USDC', x_free, new_pv)
            st.rerun()
        except Exception as e: st.error(e)
else:
    if st.button("🛑 ARRÊTER ET TOUT ANNULER", use_container_width=True):
        try: k.cancel_all_orders('XRP/USDC')
        except: pass
        bot["status"] = "OFF"
        st.rerun()

# --- 8. MOTEUR ---
if bot["status"] == "ON":
    @st.fragment(run_every=15)
    def engine():
        try:
            orders_live = k.fetch_open_orders('XRP/USDC')
            if not orders_live:
                play_notification_sound()
                st.balloons()
                bal_now = k.fetch_balance()
                u, x = bal_now['free'].get('USDC', 0.0), bal_now['free'].get('XRP', 0.0)
                if x > 5.0:
                    k.create_limit_sell_order('XRP/USDC', x, bot["pv"])
                elif u > 7.0:
                    vol = float(k.amount_to_precision('XRP/USDC', u / bot["pa"]))
                    k.create_limit_buy_order('XRP/USDC', vol, bot["pa"], {'post-only': True})
                st.rerun()
        except: pass
    engine()
