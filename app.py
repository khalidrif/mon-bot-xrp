import streamlit as st
import ccxt
import time

# 1. CONFIGURATION
st.set_page_config(page_title="XRP Manual Levels", layout="wide")
st.title("🎯 Bot XRP/USDC - Niveaux Fixes")

# Connexion Kraken via Secrets
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
except:
    st.error("Erreur API. Vérifiez vos Secrets.")
    st.stop()

# 2. SAISIE MANUELLE DES PRIX (Sidebar)
with st.sidebar:
    st.header("📍 Vos Niveaux")
    symbol = "XRP/USDC"
    
    # On récupère le prix actuel pour aider à la saisie
    ticker_init = exchange.fetch_ticker(symbol)
    prix_actuel_init = ticker_init['last']
    st.write(f"Prix actuel : **{prix_actuel_init:.4f}**")
    
    # Saisie manuelle des seuils
    prix_achat_manuel = st.number_input("Prix d'ACHAT cible (USDC)", value=prix_actuel_init * 0.98, format="%.4f")
    prix_vente_manuel = st.number_input("Prix de VENTE cible (USDC)", value=prix_actuel_init * 1.02, format="%.4f")
    
    st.divider()
    mise_usdc = st.number_input("Mise pour l'achat (USDC)", min_value=10.0, value=20.0)

# 3. ÉTAT DU BOT
if 'actif' not in st.session_state: st.session_state.actif = False

# 4. CONTRÔLES
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LA SURVEILLANCE", type="primary", use_container_width=True):
    st.session_state.actif = True

if c2.button("🛑 ARRÊTER", use_container_width=True):
    st.session_state.actif = False

st.divider()

# 5. BOUCLE LIVE
if st.session_state.actif:
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp_bal = bal['free'].get('XRP', 0.0)
        usdc_bal = bal['free'].get('USDC', 0.0)

        # AFFICHAGE DES MÉTRIQUES
        m1, m2, m3 = st.columns(3)
        
        # Calcul de l'écart restant
        dist_achat = ((price - prix_achat_manuel) / prix_achat_manuel) * 100
        dist_vente = ((prix_vente_manuel - price) / price) * 100

        m1.metric("Prix XRP Actuel", f"{price:.4f} USDC")
        m2.metric("🎯 Objectif VENTE", f"{prix_vente_manuel:.4f}", f"-{dist_vente:.2f}% avant cible", delta_color="inverse")
        m3.metric("📉 Objectif ACHAT", f"{prix_achat_manuel:.4f}", f"{dist_achat:.2f}% avant cible")

        st.info(f"💰 Portefeuille : {usdc_bal:.2f} USDC | {xrp_bal:.2f} XRP")

        # --- LOGIQUE D'EXÉCUTION SUR PRIX FIXES ---

        # 1. Condition de Vente
        if price >= prix_vente_manuel and xrp_bal > 10:
            st.balloons()
            st.success(f"💰 PRIX DE VENTE ATTEINT ({price}) ! Vente en cours...")
            exchange.create_market_sell_order(symbol, xrp_bal)
            st.session_state.actif = False # On arrête après l'exécution pour sécurité
            st.rerun()

        # 2. Condition d'Achat
        elif price <= prix_achat_manuel and usdc_bal >= mise_usdc:
            st.warning(f"🛒 PRIX D'ACHAT ATTEINT ({price}) ! Achat en cours...")
            qty = mise_usdc / price
            exchange.create_market_buy_order(symbol, qty)
            st.session_state.actif = False # On arrête pour te laisser fixer le nouveau prix de vente
            st.rerun()

        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur : {e}")
        time.sleep(10)
        st.rerun()
else:
    st.info("Bot en attente. Saisissez vos prix cibles à gauche et cliquez sur DÉMARRER.")
