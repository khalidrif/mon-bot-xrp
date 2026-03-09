import streamlit as st
import ccxt
import time

# 1. CONFIGURATION ET SECRETS
st.set_page_config(page_title="XRP Real Trading Bot", layout="wide")
st.title("🚀 Bot de Trading XRP/USDC - LIVE")

# Connexion Kraken via Secrets
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
except Exception as e:
    st.error("Erreur de connexion API. Vérifiez vos Secrets Streamlit.")
    st.stop()

# 2. SAISIE DES PARAMÈTRES (Sidebar)
with st.sidebar:
    st.header("⚙️ Réglages")
    symbol = st.text_input("Paire", value="XRP/USDC")
    stake_amount = st.number_input("Montant d'achat (USDC)", min_value=10.0, value=20.0)
    profit_target = st.slider("Objectif Profit (%)", 0.5, 10.0, 2.0) / 100
    dip_threshold = st.slider("Rachat si baisse de (%)", 0.5, 10.0, 1.5) / 100

# 3. ÉTAT DU BOT
if 'bot_actif' not in st.session_state:
    st.session_state.bot_actif = False
if 'last_buy_price' not in st.session_state:
    st.session_state.last_buy_price = 0.0

# 4. CONTRÔLES
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LE TRADING RÉEL", type="primary", use_container_width=True):
    st.session_state.bot_actif = True
if c2.button("🛑 ARRÊTER", use_container_width=True):
    st.session_state.bot_actif = False

st.divider()

# 5. BOUCLE DE TRADING LIVE
if st.session_state.bot_actif:
    try:
        # Infos Marché & Compte
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp_bal = bal['free'].get('XRP', 0.0)
        usdc_bal = bal['free'].get('USDC', 0.0)

        # Affichage Métriques
        m1, m2, m3 = st.columns(3)
        m1.metric("Prix XRP", f"{price} USDC")
        m2.metric("Solde XRP", f"{xrp_bal:.2f}")
        m3.metric("Solde USDC", f"{usdc_bal:.2f}")

        # Initialisation du premier prix d'achat si vide
        if st.session_state.last_buy_price == 0.0:
            st.session_state.last_buy_price = price

        # CALCULS DE STRATÉGIE
        diff_pct = (price - st.session_state.last_buy_price) / st.session_state.last_buy_price

        # --- CONDITION DE VENTE (PROFIT) ---
        if diff_pct >= profit_target and xrp_bal > 5:
            st.balloons()
            st.success(f"💰 VENTE : Profit de {diff_pct:.2%} atteint !")
            # ORDRE RÉEL DE VENTE
            exchange.create_market_sell_order(symbol, xrp_bal)
            st.session_state.last_buy_price = price # Reset pour prochain cycle
            time.sleep(5)

        # --- CONDITION D'ACHAT (BAISSE / BOULE DE NEIGE) ---
        elif diff_pct <= -dip_threshold and usdc_bal >= stake_amount:
            st.warning(f"📉 ACHAT : Baisse de {diff_pct:.2%} détectée. Accumulation !")
            # ORDRE RÉEL D'ACHAT
            quantity = stake_amount / price
            exchange.create_market_buy_order(symbol, quantity)
            st.session_state.last_buy_price = price # Nouveau prix moyen
            time.sleep(5)

        st.info(f"Dernière vérification : {time.strftime('%H:%M:%S')} | Écart : {diff_pct:.2%}")
        
        # Rafraîchissement automatique
        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur Trading : {e}")
        time.sleep(20)
        st.rerun()
else:
    st.info("Le bot est en attente. Cliquez sur DÉMARRER pour activer les ordres réels.")
