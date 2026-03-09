import streamlit as st
import ccxt
import time

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="XRP Verrouillé Bot", layout="wide")
st.title("🤖 Bot XRP/USDC - Niveaux Fixes & Verrouillés")

# --- CONNEXION KRAKEN ---
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    symbol = "XRP/USDC"
except Exception as e:
    st.error(f"Erreur API : {e}")
    st.stop()

# --- MÉMOIRE DES PRIX (SESSION STATE) ---
# On initialise les prix une seule fois au tout premier chargement
if 'prix_achat' not in st.session_state or 'prix_vente' not in st.session_state:
    try:
        ticker_init = exchange.fetch_ticker(symbol)
        st.session_state.prix_achat = ticker_init['last'] * 0.99
        st.session_state.prix_vente = ticker_init['last'] * 1.02
    except:
        st.session_state.prix_achat = 0.5000
        st.session_state.prix_vente = 0.6000

if 'actif' not in st.session_state:
    st.session_state.actif = False

# --- BARRE LATÉRALE (SAISIE) ---
with st.sidebar:
    st.header("📍 Vos Niveaux Manuels")
    
    # Affichage du prix actuel pour aide
    ticker_now = exchange.fetch_ticker(symbol)
    st.write(f"Prix actuel marché : **{ticker_now['last']:.4f}**")
    st.divider()

    # Saisies liées à la mémoire (Session State)
    st.session_state.prix_achat = st.number_input(
        "Prix d'ACHAT (USDC)", 
        value=st.session_state.prix_achat, 
        format="%.4f",
        help="Le bot achètera quand le prix sera INFÉRIEUR à ce niveau."
    )
    
    st.session_state.prix_vente = st.number_input(
        "Prix de VENTE (USDC)", 
        value=st.session_state.prix_vente, 
        format="%.4f",
        help="Le bot vendra quand le prix sera SUPÉRIEUR à ce niveau."
    )
    
    mise_usdc = st.number_input("Mise par achat (USDC)", min_value=10.0, value=20.0)
    st.info("💡 Vos prix sont verrouillés. Ils ne changeront pas lors des rafraîchissements.")

# --- INTERFACE PRINCIPALE ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LA SURVEILLANCE", type="primary", use_container_width=True):
    st.session_state.actif = True

if c2.button("🛑 ARRÊTER", use_container_width=True):
    st.session_state.actif = False

st.divider()

if st.session_state.actif:
    try:
        # Données Live
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp_bal = bal['free'].get('XRP', 0.0)
        usdc_bal = bal['free'].get('USDC', 0.0)

        # Affichage des métriques
        m1, m2, m3 = st.columns(3)
        m1.metric("Prix XRP Actuel", f"{price:.4f} USDC")
        m2.metric("🎯 Objectif VENTE", f"{st.session_state.prix_vente:.4f}")
        m3.metric("📉 Objectif ACHAT", f"{st.session_state.prix_achat:.4f}")

        st.write(f"💰 Portefeuille : **{usdc_bal:.2f} USDC** | **{xrp_bal:.2f} XRP**")

        # --- LOGIQUE D'EXÉCUTION ---

        # 1. ACHAT
        if price <= st.session_state.prix_achat:
            if usdc_bal >= mise_usdc:
                st.warning("🛒 Niveau d'achat atteint. Exécution...")
                qty = float(exchange.amount_to_precision(symbol, mise_usdc / price))
                order = exchange.create_market_buy_order(symbol, qty)
                st.success(f"✅ ACHAT RÉUSSI ! ID: {order['id']}")
                st.session_state.actif = False # Sécurité : arrêt après achat
                st.rerun()
            else:
                st.error("Solde USDC insuffisant.")

        # 2. VENTE
        elif price >= st.session_state.prix_vente:
            if xrp_bal > 10:
                st.success("💰 Niveau de vente atteint. Profit...")
                qty_sell = float(exchange.amount_to_precision(symbol, xrp_bal))
                order = exchange.create_market_sell_order(symbol, qty_sell)
                st.balloons()
                st.success(f"✅ VENTE RÉUSSIE ! ID: {order['id']}")
                st.session_state.actif = False # Sécurité : arrêt après vente
                st.rerun()
            else:
                st.error("Solde XRP insuffisant pour vendre.")

        # Rafraîchissement
        st.info(f"Dernière vérification : {time.strftime('%H:%M:%S')}")
        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur Kraken : {e}")
        time.sleep(15)
        st.rerun()
else:
    st.info("Bot en attente. Réglez vos prix à gauche et cliquez sur DÉMARRER.")
