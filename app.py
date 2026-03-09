import streamlit as st
import ccxt
import time

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="XRP Final Bot", layout="wide")
st.title("🚀 Bot XRP/USDC - Trading Réel (Niveaux Fixes)")

# --- CONNEXION KRAKEN (Secrets) ---
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
except Exception as e:
    st.error(f"Erreur API : {e}")
    st.stop()

# --- SAISIE DES PARAMÈTRES (Sidebar) ---
with st.sidebar:
    st.header("📍 Vos Niveaux Manuels")
    symbol = "XRP/USDC"
    
    # Récupération du prix actuel pour aider à la saisie
    try:
        ticker_init = exchange.fetch_ticker(symbol)
        prix_actuel_init = ticker_init['last']
        st.write(f"Prix actuel du marché : **{prix_actuel_init:.4f}**")
    except:
        prix_actuel_init = 0.5000 # Valeur par défaut si erreur réseau

    # Champs de saisie
    prix_achat_cible = st.number_input("Prix d'ACHAT (USDC)", value=prix_actuel_init * 0.99, format="%.4f")
    prix_vente_cible = st.number_input("Prix de VENTE (USDC)", value=prix_actuel_init * 1.02, format="%.4f")
    mise_usdc = st.number_input("Mise par achat (min 15 USDC)", min_value=10.0, value=20.0)

# --- ÉTAT DU BOT ---
if 'actif' not in st.session_state:
    st.session_state.actif = False

# --- BOUTONS ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LA SURVEILLANCE", type="primary", use_container_width=True):
    st.session_state.actif = True

if c2.button("🛑 ARRÊTER", use_container_width=True):
    st.session_state.actif = False

st.divider()

# --- BOUCLE DE TRADING ---
if st.session_state.actif:
    try:
        # 1. Infos en direct
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp_bal = bal['free'].get('XRP', 0.0)
        usdc_bal = bal['free'].get('USDC', 0.0)

        # 2. Affichage des Métriques
        m1, m2, m3 = st.columns(3)
        m1.metric("Prix XRP", f"{price:.4f} USDC")
        m2.metric("🎯 VENTE à", f"{prix_vente_cible:.4f}")
        m3.metric("📉 ACHAT à", f"{prix_achat_cible:.4f}")
        
        st.write(f"💰 Portefeuille : **{usdc_bal:.2f} USDC** | **{xrp_bal:.2f} XRP**")

        # --- LOGIQUE D'ACHAT ---
        if price <= prix_achat_cible:
            if usdc_bal >= mise_usdc:
                st.warning(f"🛒 Prix d'achat touché ({price}). Exécution...")
                
                # Calcul de la quantité avec précision Kraken
                raw_qty = mise_usdc / price
                qty = float(exchange.amount_to_precision(symbol, raw_qty))
                
                # ORDRE RÉEL
                order = exchange.create_market_buy_order(symbol, qty)
                st.success(f"✅ ACHAT EFFECTUÉ ! ID: {order['id']}")
                st.session_state.actif = False # Arrêt pour sécurité
                st.rerun()
            else:
                st.error("Solde USDC insuffisant pour l'achat.")

        # --- LOGIQUE DE VENTE ---
        elif price >= prix_vente_cible:
            if xrp_bal > 10: # Minimum de sécurité pour vendre
                st.success(f"💰 Prix de vente touché ({price}). Profit en cours...")
                
                # Précision pour la vente
                qty_to_sell = float(exchange.amount_to_precision(symbol, xrp_bal))
                
                # ORDRE RÉEL
                order = exchange.create_market_sell_order(symbol, qty_to_sell)
                st.balloons()
                st.success(f"✅ VENTE EFFECTUÉE ! ID: {order['id']}")
                st.session_state.actif = False # Arrêt pour sécurité
                st.rerun()
            else:
                st.error("Pas assez de XRP pour vendre (min ~10 XRP).")

        # 3. Rafraîchissement automatique
        st.info(f"Dernière vérification : {time.strftime('%H:%M:%S')}")
        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur Kraken : {e}")
        time.sleep(15)
        st.rerun()
else:
    st.info("Bot en attente. Configurez vos prix à gauche et cliquez sur DÉMARRER.")
