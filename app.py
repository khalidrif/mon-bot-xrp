import streamlit as st
import ccxt
import time

# 1. CONFIGURATION
st.set_page_config(page_title="XRP Auto Trader", layout="wide")
st.title("🚀 Bot XRP/USDC - Trading Automatique Réel")

# Connexion via Secrets Streamlit
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
except:
    st.error("Erreur de connexion API. Vérifiez vos Secrets.")
    st.stop()

# 2. PARAMÈTRES (Sidebar)
with st.sidebar:
    st.header("⚙️ Réglages Stratégie")
    symbol = "XRP/USDC"
    stake_amount = st.number_input("Mise par achat (USDC)", min_value=10.0, value=20.0)
    profit_target = st.slider("Objectif Profit (%)", 0.5, 5.0, 2.0) / 100
    dip_threshold = st.slider("Rachat si baisse (%)", 0.5, 5.0, 1.5) / 100

# 3. ÉTAT DE LA SESSION (Mémoire du Bot)
if 'actif' not in st.session_state: st.session_state.actif = False
if 'last_buy_price' not in st.session_state: st.session_state.last_buy_price = 0.0

# 4. CONTRÔLES
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LE TRADING RÉEL", type="primary", use_container_width=True):
    st.session_state.actif = True
    st.toast("Bot activé !")

if c2.button("🛑 ARRÊTER", use_container_width=True):
    st.session_state.actif = False
    st.toast("Bot arrêté.")

st.divider()

# 5. BOUCLE DE SURVEILLANCE
if st.session_state.actif:
    try:
        # Récupération des données Live
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp_bal = bal['free'].get('XRP', 0.0)
        usdc_bal = bal['free'].get('USDC', 0.0)

        # Initialisation du prix de référence au premier lancement
        if st.session_state.last_buy_price == 0.0:
            st.session_state.last_buy_price = price

        # CALCUL DES CIBLES
        prix_vente = st.session_state.last_buy_price * (1 + profit_target)
        prix_achat = st.session_state.last_buy_price * (1 - dip_threshold)
        diff_pct = (price - st.session_state.last_buy_price) / st.session_state.last_buy_price

        # AFFICHAGE DES MÉTRIQUES
        st.subheader("📊 Tableau de bord en direct")
        m1, m2, m3 = st.columns(3)
        m1.metric("Prix XRP actuel", f"{price:.4f} USDC", f"{diff_pct:.2%}")
        m2.metric("🎯 Cible VENTE", f"{prix_vente:.4f} USDC", f"+{profit_target*100}%")
        m3.metric("📉 Cible ACHAT", f"{prix_achat:.4f} USDC", f"-{dip_threshold*100}%")

        st.info(f"💰 Solde : {usdc_bal:.2f} USDC | {xrp_bal:.2f} XRP")

        # --- LOGIQUE D'EXÉCUTION RÉELLE ---
        
        # CAS VENTE (On prend le profit)
        if price >= prix_vente and xrp_bal > 10:
            st.balloons()
            st.success("💰 Profit atteint ! Vente en cours...")
            exchange.create_market_sell_order(symbol, xrp_bal)
            st.session_state.last_buy_price = price # Reset référence
            time.sleep(5)
            st.rerun()

        # CAS ACHAT (On accumule dans la baisse)
        elif price <= prix_achat and usdc_bal >= stake_amount:
            st.warning("❄️ Baisse détectée ! Achat Boule de neige...")
            qty = stake_amount / price
            exchange.create_market_buy_order(symbol, qty)
            st.session_state.last_buy_price = price # Nouveau prix de référence
            time.sleep(5)
            st.rerun()

        # Rafraîchissement toutes les 30 secondes
        st.write(f"Dernière vérification : {time.strftime('%H:%M:%S')}")
        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur : {e}")
        time.sleep(10)
        st.rerun()
else:
    st.info("Le bot est à l'arrêt. Cliquez sur DÉMARRER pour lancer le trading réel.")
