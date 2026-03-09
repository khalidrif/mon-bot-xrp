import streamlit as st
import ccxt
import time

# 1. CONFIGURATION ET SECRETS
st.set_page_config(page_title="XRP Live Trader", layout="wide")
st.title("🚀 Bot XRP/USDC - Suivi des Objectifs")

# Connexion Kraken
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True
    })
except:
    st.error("Erreur API. Vérifiez vos Secrets.")
    st.stop()

# 2. RÉGLAGES (Sidebar)
with st.sidebar:
    st.header("⚙️ Paramètres")
    symbol = st.text_input("Paire", value="XRP/USDC")
    stake_amount = st.number_input("Mise (USDC)", min_value=10.0, value=20.0)
    profit_target = st.slider("Objectif Profit (%)", 0.5, 10.0, 2.0) / 100
    dip_threshold = st.slider("Rachat si baisse (%)", 0.5, 10.0, 1.5) / 100

# 3. ÉTAT DU BOT
if 'bot_actif' not in st.session_state:
    st.session_state.bot_actif = False
if 'last_buy_price' not in st.session_state:
    st.session_state.last_buy_price = 0.0

# 4. CONTRÔLES
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER", type="primary", use_container_width=True):
    st.session_state.bot_actif = True
if c2.button("🛑 ARRÊTER", use_container_width=True):
    st.session_state.bot_actif = False

st.divider()

# 5. BOUCLE DE TRADING LIVE
if st.session_state.bot_actif:
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp_bal = bal['free'].get('XRP', 0.0)

        # Si c'est le premier lancement, on prend le prix actuel comme référence
        if st.session_state.last_buy_price == 0.0:
            st.session_state.last_buy_price = price

        # --- CALCUL DES PRIX CIBLES ---
        prix_vente_cible = st.session_state.last_buy_price * (1 + profit_target)
        prix_achat_suivant = st.session_state.last_buy_price * (1 - dip_threshold)
        diff_pct = (price - st.session_state.last_buy_price) / st.session_state.last_buy_price

        # --- AFFICHAGE DES MÉTRIQUES ---
        st.subheader("📊 État du Marché")
        m1, m2, m3 = st.columns(3)
        m1.metric("Prix Actuel XRP", f"{price:.4f} USDC", f"{diff_pct:.2%}")
        m2.metric("🎯 Prochaine VENTE à", f"{prix_vente_cible:.4f} USDC", f"+{profit_target:.1%}")
        m3.metric("📉 Prochain ACHAT à", f"{prix_achat_suivant:.4f} USDC", f"-{dip_threshold:.1%}")

        st.divider()
        
        st.info(f"Prix de référence (dernier achat) : **{st.session_state.last_buy_price:.4f} USDC**")

        # --- LOGIQUE D'EXÉCUTION ---
        if price >= prix_vente_cible and xrp_bal > 5:
            st.success("💰 VENTE EXÉCUTÉE !")
            exchange.create_market_sell_order(symbol, xrp_bal)
            st.session_state.last_buy_price = price 
            time.sleep(5)
            st.rerun()

        elif price <= prix_achat_suivant:
            st.warning("❄️ ACHAT BOULE DE NEIGE EXÉCUTÉ !")
            quantity = stake_amount / price
            exchange.create_market_buy_order(symbol, quantity)
            st.session_state.last_buy_price = price
            time.sleep(5)
            st.rerun()

        # Rafraîchissement automatique
        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur : {e}")
        time.sleep(10)
        st.rerun()
else:
    st.info("Bot à l'arrêt. Les prix cibles s'afficheront au démarrage.")
