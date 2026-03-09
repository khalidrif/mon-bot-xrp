import streamlit as st
import ccxt
import time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Infinite Bot", layout="wide")
st.title("🤖 Bot XRP/USDC - Boule de Neige Infinie")

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

# --- MÉMOIRE ---
if 'actif' not in st.session_state:
    st.session_state.actif = False

if 'p_achat' not in st.session_state:
    ticker = exchange.fetch_ticker(symbol)
    st.session_state.p_achat = ticker['last'] * 0.98
    st.session_state.p_vente = ticker['last'] * 1.02

# --- RÉGLAGES ---
with st.sidebar:
    st.header("📍 Niveaux de Trading")
    st.session_state.p_achat = st.number_input("Prix ACHAT", value=st.session_state.p_achat, format="%.4f")
    st.session_state.p_vente = st.number_input("Prix VENTE", value=st.session_state.p_vente, format="%.4f")
    mise_usdc = st.number_input("Mise (USDC)", min_value=10.0, value=20.0)
    st.info("🔄 Le bot continuera de tourner après chaque transaction.")

# --- BOUTONS ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LA BOUCLE INFINIE", type="primary", use_container_width=True):
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

        # Affichage
        m1, m2, m3 = st.columns(3)
        m1.metric("Prix XRP Actuel", f"{price:.4f} USDC")
        m2.metric("🎯 VENTE Cible", f"{st.session_state.p_vente:.4f}")
        m3.metric("📉 ACHAT Cible", f"{st.session_state.p_achat:.4f}")
        
        st.success(f"✅ BOT ACTIF - Dernière analyse : {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"Portefeuille : **{usdc_bal:.2f} USDC** | **{xrp_bal:.2f} XRP**")

        # --- LOGIQUE D'EXÉCUTION (SANS ARRÊT) ---
        
        # 1. ACHAT
        if price <= st.session_state.p_achat and usdc_bal >= mise_usdc:
            st.warning("⚡ ACHAT EN COURS...")
            qty = float(exchange.amount_to_precision(symbol, mise_usdc / price))
            exchange.create_market_buy_order(symbol, qty)
            st.balloons()
            # On ne met PAS st.session_state.actif = False ici pour qu'il continue !
            time.sleep(10) # Pause de sécurité
            st.rerun()

        # 2. VENTE
        elif price >= st.session_state.p_vente and xrp_bal > 10:
            st.success("💰 VENTE EN COURS...")
            qty_sell = float(exchange.amount_to_precision(symbol, xrp_bal))
            exchange.create_market_sell_order(symbol, qty_sell)
            st.balloons()
            # On ne met PAS st.session_state.actif = False ici !
            time.sleep(10) # Pause de sécurité
            st.rerun()

        # Attente normale entre les vérifications
        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur : {e}")
        time.sleep(20)
        st.rerun()
else:
    st.error("❌ LE BOT EST À L'ARRÊT.")
