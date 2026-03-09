import streamlit as st
import ccxt
import time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Infinite Bot", layout="wide")
st.title("🤖 Bot XRP/USDC - Boucle Alternée")

# Connexion Kraken
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

# --- MÉMOIRE / ÉTAT DU BOT ---
if 'actif' not in st.session_state:
    st.session_state.actif = False

# Cette variable empêche d'acheter plusieurs fois de suite
if 'etape' not in st.session_state:
    st.session_state.etape = "ATTENTE_ACHAT"

if 'p_achat' not in st.session_state:
    ticker = exchange.fetch_ticker(symbol)
    st.session_state.p_achat = ticker['last'] * 0.995
    st.session_state.p_vente = ticker['last'] * 1.005

# --- RÉGLAGES ---
with st.sidebar:
    st.header("📍 Paramètres")
    st.session_state.p_achat = st.number_input("Prix ACHAT Cible", value=st.session_state.p_achat, format="%.4f")
    st.session_state.p_vente = st.number_input("Prix VENTE Cible", value=st.session_state.p_vente, format="%.4f")
    mise_usdc = st.number_input("Mise par achat (USDC)", min_value=10.0, value=20.0)
    
    st.divider()
    st.write(f"Statut actuel : **{st.session_state.etape}**")
    if st.button("Réinitialiser l'étape (Achat)"):
        st.session_state.etape = "ATTENTE_ACHAT"
        st.rerun()

# --- BOUTONS DE CONTRÔLE ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LE BOT", type="primary", use_container_width=True):
    st.session_state.actif = True

if c2.button("🛑 ARRÊTER LE BOT", use_container_width=True):
    st.session_state.actif = False

st.divider()

# --- BOUCLE DE TRADING ---
if st.session_state.actif:
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp_bal = bal['free'].get('XRP', 0.0)
        usdc_bal = bal['free'].get('USDC', 0.0)

        # Affichage des métriques
        m1, m2, m3 = st.columns(3)
        m1.metric("Prix XRP Actuel", f"{price:.4f} USDC")
        m2.metric("🎯 Objectif Vente", f"{st.session_state.p_vente:.4f}")
        m3.metric("📉 Objectif Achat", f"{st.session_state.p_achat:.4f}")
        
        st.info(f"Mode : **{st.session_state.etape}** | Dernière analyse : {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"Portefeuille : **{usdc_bal:.2f} USDC** | **{xrp_bal:.2f} XRP**")

        # --- LOGIQUE D'EXÉCUTION ---
        
        # 1. ACHAT : Seulement si on attend un achat ET que le prix est bas
        if st.session_state.etape == "ATTENTE_ACHAT" and price <= st.session_state.p_achat:
            if usdc_bal >= mise_usdc:
                st.warning("⚡ Exécution ACHAT...")
                qty = float(exchange.amount_to_precision(symbol, mise_usdc / price))
                exchange.create_market_buy_order(symbol, qty)
                st.session_state.etape = "ATTENTE_VENTE" # On change l'étape
                st.balloons()
                time.sleep(5)
                st.rerun()
            else:
                st.error("Solde USDC insuffisant pour acheter.")

        # 2. VENTE : Seulement si on attend une vente ET que le prix est haut
        elif st.session_state.etape == "ATTENTE_VENTE" and price >= st.session_state.p_vente:
            if xrp_bal > 5: # On vérifie qu'on a bien reçu les XRP
                st.success("💰 Exécution VENTE...")
                # On vend tout le XRP disponible
                qty_sell = float(exchange.amount_to_precision(symbol, xrp_bal * 0.99)) 
                exchange.create_market_sell_order(symbol, qty_sell)
                st.session_state.etape = "ATTENTE_ACHAT" # On revient au début
                st.balloons()
                time.sleep(5)
                st.rerun()

        # Attente avant rafraîchissement
        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur : {e}")
        time.sleep(30)
        st.rerun()
else:
    st.warning("Le bot est en pause. Cliquez sur Démarrer.")
