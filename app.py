import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ET CONNEXION ---
st.set_page_config(page_title="XRP Bot Full Auto", layout="wide")
st.title("🤖 Bot XRP/USDC - Surveillance Continue")

try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    symbol = "XRP/USDC"
except Exception as e:
    st.error(f"Erreur de connexion API : {e}")
    st.stop()

# --- 2. GESTION DE LA MÉMOIRE (SESSION STATE) ---
if 'actif' not in st.session_state:
    st.session_state.actif = False

# Initialisation des prix cibles une seule fois
if 'p_achat' not in st.session_state or 'p_vente' not in st.session_state:
    try:
        ticker = exchange.fetch_ticker(symbol)
        st.session_state.p_achat = ticker['last'] * 0.98
        st.session_state.p_vente = ticker['last'] * 1.02
    except:
        st.session_state.p_achat = 0.5000
        st.session_state.p_vente = 0.6000

# --- 3. BARRE LATÉRALE (RÉGLAGES FIXES) ---
with st.sidebar:
    st.header("📍 Paramètres Verrouillés")
    
    # Ces champs modifient la mémoire de la session
    st.session_state.p_achat = st.number_input("Prix ACHAT cible", value=st.session_state.p_achat, format="%.4f")
    st.session_state.p_vente = st.number_input("Prix VENTE cible", value=st.session_state.p_vente, format="%.4f")
    mise_usdc = st.number_input("Mise (USDC)", min_value=10.0, value=20.0)
    
    st.divider()
    st.info("💡 Le bot compare le prix réel à ces paliers toutes les 30 secondes.")

# --- 4. BOUTONS DE CONTRÔLE ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LA BOUCLE", type="primary", use_container_width=True):
    st.session_state.actif = True

if c2.button("🛑 ARRÊTER LE BOT", use_container_width=True):
    st.session_state.actif = False
    st.warning("Le bot s'arrêtera après le cycle en cours.")

st.divider()

# --- 5. ZONE D'AFFICHAGE DYNAMIQUE ---
status_zone = st.empty()
metrics_zone = st.container()

# --- 6. LA BOUCLE DE TRADING ---
if st.session_state.actif:
    try:
        # Récupération des données
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp_bal = bal['free'].get('XRP', 0.0)
        usdc_bal = bal['free'].get('USDC', 0.0)

        # Mise à jour de l'affichage
        with metrics_zone:
            m1, m2, m3 = st.columns(3)
            m1.metric("Prix XRP Actuel", f"{price:.4f} USDC")
            m2.metric("🎯 Cible VENTE", f"{st.session_state.p_vente:.4f}")
            m3.metric("📉 Cible ACHAT", f"{st.session_state.p_achat:.4f}")
            st.write(f"💰 **Solde :** {usdc_bal:.2f} USDC | {xrp_bal:.2f} XRP")

        status_zone.success(f"✅ BOUCLE ACTIVE - Dernière vérification : {datetime.now().strftime('%H:%M:%S')}")

        # --- LOGIQUE D'EXÉCUTION RÉELLE ---
        
        # ACHAT
        if price <= st.session_state.p_achat and usdc_bal >= mise_usdc:
            st.warning("⚡ SEUIL D'ACHAT TOUCHÉ ! Exécution...")
            qty = float(exchange.amount_to_precision(symbol, mise_usdc / price))
            exchange.create_market_buy_order(symbol, qty)
            st.balloons()
            st.session_state.actif = False # Sécurité : arrêt pour recalibrer
            st.rerun()

        # VENTE
        elif price >= st.session_state.p_vente and xrp_bal > 10:
            st.success("💰 SEUIL DE VENTE TOUCHÉ ! Profit...")
            qty_sell = float(exchange.amount_to_precision(symbol, xrp_bal))
            exchange.create_market_sell_order(symbol, qty_sell)
            st.balloons()
            st.session_state.actif = False # Sécurité
            st.rerun()

        # --- ATTENTE AVANT PROCHAIN CYCLE ---
        time.sleep(30) 
        st.rerun() # RELANCE LA BOUCLE AUTOMATIQUEMENT

    except Exception as e:
        st.error(f"Erreur réseau ou Kraken : {e}")
        time.sleep(20)
        st.rerun()

else:
    status_zone.error("❌ LE BOT EST ACTUELLEMENT À L'ARRÊT.")
