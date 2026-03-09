import streamlit as st
import ccxt
import time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Limit Bot", layout="wide")
st.title("🤖 Bot XRP - Diagnostic & Exécution")

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

# --- MÉMOIRE ---
if 'actif' not in st.session_state:
    st.session_state.actif = False
if 'etape' not in st.session_state:
    st.session_state.etape = "ATTENTE_ACHAT"

# --- RÉGLAGES ---
with st.sidebar:
    st.header("⚙️ Stratégie")
    p_achat = st.number_input("Prix ACHAT (LIMIT)", value=1.3620, format="%.4f")
    p_vente = st.number_input("Prix VENTE (LIMIT)", value=1.3850, format="%.4f")
    mise_usdc = st.number_input("Mise (USDC)", min_value=10.0, value=20.0)
    
    st.divider()
    if st.button("🔄 Reset à ACHAT"):
        st.session_state.etape = "ATTENTE_ACHAT"
        st.rerun()

# --- BOUTONS ---
c1, c2 = st.columns(2)
if c1.button("🚀 LANCER LE BOT", type="primary", use_container_width=True):
    st.session_state.actif = True
if c2.button("🛑 STOP", use_container_width=True):
    st.session_state.actif = False

st.divider()

# --- LOGIQUE DE TRADING ---
if st.session_state.actif:
    try:
        # 1. RÉCUPÉRATION DES PRIX (Affiché en priorité)
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        
        # Affichage constant des prix
        col1, col2, col3 = st.columns(3)
        col1.metric("Prix XRP Actuel", f"{price:.4f} USDC")
        col2.metric("Objectif Achat", f"{p_achat:.4f}")
        col3.metric("État du Bot", st.session_state.etape)

        # 2. VÉRIFICATION DES SOLDES
        bal = exchange.fetch_balance()
        usdc_bal = bal['free'].get('USDC', 0.0)
        xrp_bal = bal['free'].get('XRP', 0.0)
        st.write(f"💰 Portefeuille : **{usdc_bal:.2f} USDC** | **{xrp_bal:.2f} XRP**")

        # 3. LOGIQUE D'ACHAT
        if st.session_state.etape == "ATTENTE_ACHAT" and price <= p_achat:
            if usdc_bal >= mise_usdc:
                st.warning(f"⏳ Tentative d'achat à {p_achat}...")
                qty = float(exchange.amount_to_precision(symbol, mise_usdc / p_achat))
                
                # ENVOI RÉEL À KRAKEN (avec capture d'erreur)
                try:
                    ordre = exchange.create_limit_buy_order(symbol, qty, p_achat)
                    st.success(f"✅ ORDRE KRAKEN REÇU : ID {ordre['id']}")
                    st.session_state.etape = "ATTENTE_VENTE"
                    time.sleep(5) 
                    st.rerun()
                except Exception as e_api:
                    st.error(f"❌ KRAKEN A REFUSÉ L'ACHAT : {e_api}")
            else:
                st.error("❌ Solde USDC insuffisant sur Kraken !")

        # 4. LOGIQUE DE VENTE
        elif st.session_state.etape == "ATTENTE_VENTE" and price >= p_vente:
            if xrp_bal > 1: # Minimum de sécurité
                st.warning(f"⏳ Tentative de vente à {p_vente}...")
                qty_sell = float(exchange.amount_to_precision(symbol, xrp_bal * 0.995))
                
                try:
                    ordre = exchange.create_limit_sell_order(symbol, qty_sell, p_vente)
                    st.success(f"✅ VENTE KRAKEN REÇUE : ID {ordre['id']}")
                    st.session_state.etape = "ATTENTE_ACHAT"
                    st.balloons()
                    time.sleep(10)
                    st.rerun()
                except Exception as e_api:
                    st.error(f"❌ KRAKEN A REFUSÉ LA VENTE : {e_api}")

        # Pause standard
        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.error(f"⚠️ Erreur de connexion ou de lecture : {e}")
        time.sleep(10)
        st.rerun()
else:
    st.info("Bot à l'arrêt. En attente de démarrage.")
