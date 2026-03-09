import streamlit as st
import ccxt
import time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Limit Bot", layout="wide")
st.title("🤖 Bot XRP/USDC - Ordres Limit")

# Connexion Kraken
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
    })
    symbol = "XRP/USDC"
except Exception as e:
    st.error(f"Erreur API : {e}")
    st.stop()

# --- MÉMOIRE / ÉTAT ---
if 'actif' not in st.session_state:
    st.session_state.actif = False

if 'etape' not in st.session_state:
    st.session_state.etape = "ATTENTE_ACHAT"

if 'p_achat' not in st.session_state:
    ticker = exchange.fetch_ticker(symbol)
    st.session_state.p_achat = round(ticker['last'] * 0.99, 4)
    st.session_state.p_vente = round(ticker['last'] * 1.01, 4)

# --- SIDEBAR (RÉGLAGES) ---
with st.sidebar:
    st.header("📍 Paramètres Fixes")
    st.session_state.p_achat = st.number_input("Prix ACHAT (Strict)", value=st.session_state.p_achat, format="%.4f")
    st.session_state.p_vente = st.number_input("Prix VENTE (Strict)", value=st.session_state.p_vente, format="%.4f")
    mise_usdc = st.number_input("Mise (USDC)", min_value=10.0, value=20.0)
    
    st.divider()
    st.info(f"Étape : {st.session_state.etape}")
    if st.button("Forcer étape : ACHAT"):
        st.session_state.etape = "ATTENTE_ACHAT"
        st.rerun()

# --- BOUTONS ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER", type="primary", use_container_width=True):
    st.session_state.actif = True

if c2.button("🛑 ARRÊTER", use_container_width=True):
    st.session_state.actif = False

st.divider()

# --- LOGIQUE ---
if st.session_state.actif:
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp_bal = bal['free'].get('XRP', 0.0)
        usdc_bal = bal['free'].get('USDC', 0.0)

        # Affichage
        col1, col2, col3 = st.columns(3)
        col1.metric("Prix Actuel", f"{price:.4f}")
        col2.metric("Cible ACHAT", f"{st.session_state.p_achat:.4f}")
        col3.metric("Cible VENTE", f"{st.session_state.p_vente:.4f}")

        # 1. LOGIQUE ACHAT (ORDRE LIMIT)
        if st.session_state.etape == "ATTENTE_ACHAT" and price <= st.session_state.p_achat:
            if usdc_bal >= mise_usdc:
                st.warning(f"⚡ Placement ordre LIMIT ACHAT à {st.session_state.p_achat}...")
                qty = float(exchange.amount_to_precision(symbol, mise_usdc / st.session_state.p_achat))
                # On utilise create_limit_buy_order
                exchange.create_limit_buy_order(symbol, qty, st.session_state.p_achat)
                
                st.session_state.etape = "ATTENTE_VENTE"
                st.success("Ordre placé ! Passage en attente de vente.")
                time.sleep(5)
                st.rerun()

        # 2. LOGIQUE VENTE (ORDRE LIMIT)
        elif st.session_state.etape == "ATTENTE_VENTE" and price >= st.session_state.p_vente:
            if xrp_bal > 1:
                st.warning(f"💰 Placement ordre LIMIT VENTE à {st.session_state.p_vente}...")
                qty_sell = float(exchange.amount_to_precision(symbol, xrp_bal * 0.995))
                # On utilise create_limit_sell_order
                exchange.create_limit_sell_order(symbol, qty_sell, st.session_state.p_vente)
                
                st.session_state.etape = "ATTENTE_ACHAT"
                st.balloons()
                time.sleep(5)
                st.rerun()

        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur : {e}")
        time.sleep(10)
        st.rerun()
