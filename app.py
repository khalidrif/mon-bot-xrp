import streamlit as st
import ccxt
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Sniper", layout="wide")

# Connexion (Assurez-vous que vos secrets sont configurés)
@st.cache_resource
def get_exchange():
    ex = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
    })
    ex.load_markets()
    return ex

exchange = get_exchange()
symbol = "XRP/USDC"

# --- MÉMOIRE ---
if 'actif' not in st.session_state: st.session_state.actif = False
if 'etape' not in st.session_state: st.session_state.etape = "ATTENTE_ACHAT"

# --- SIDEBAR (RÉGLAGES) ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    # On stocke les entrées dans des variables pour les réutiliser
    p_achat = st.number_input("Cible ACHAT", value=1.3500, format="%.4f")
    p_vente = st.number_input("Cible VENTE", value=1.3800, format="%.4f")
    mise = st.number_input("Mise (USDC)", min_value=10.0, value=20.0)
    
    st.divider()
    st.info(f"Mode : {st.session_state.etape}")
    if st.button("🔄 Reset Bot"):
        st.session_state.etape = "ATTENTE_ACHAT"
        st.rerun()

# --- AFFICHAGE CENTRAL ---
st.title("🤖 XRP Infinite Bot")

# RÉCUPÉRATION DES DONNÉES
ticker = exchange.fetch_ticker(symbol)
price = ticker['last']
bal = exchange.fetch_balance()
usdc_bal = bal['free'].get('USDC', 0.0)
xrp_bal = bal['free'].get('XRP', 0.0)

# SECTION DES PRIX (Voici ce qui manquait)
col1, col2, col3 = st.columns(3)
col1.metric("Prix XRP Actuel", f"{price:.4f} USDC")
col2.metric("🎯 Objectif ACHAT", f"{p_achat:.4f} USDC", delta=round(price - p_achat, 4), delta_color="inverse")
col3.metric("💰 Objectif VENTE", f"{p_vente:.4f} USDC", delta=round(price - p_vente, 4))

st.write(f"💼 **Portefeuille** : {usdc_bal:.2f} USDC | {xrp_bal:.2f} XRP")
st.divider()

# --- BOUTONS ET LOGIQUE ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER", type="primary", use_container_width=True): st.session_state.actif = True
if c2.button("🛑 STOP", use_container_width=True): st.session_state.actif = False

if st.session_state.actif:
    # Logique d'achat
    if st.session_state.etape == "ATTENTE_ACHAT" and price <= p_achat:
        if usdc_bal >= mise:
            q = float(exchange.amount_to_precision(symbol, mise / p_achat))
            exchange.create_limit_buy_order(symbol, q, p_achat)
            st.session_state.etape = "ATTENTE_VENTE"
            st.rerun()
            
    # Logique de vente
    elif st.session_state.etape == "ATTENTE_VENTE" and price >= p_vente:
        if xrp_bal > 1:
            q_v = float(exchange.amount_to_precision(symbol, xrp_bal * 0.995))
            exchange.create_limit_sell_order(symbol, q_v, p_vente)
            st.session_state.etape = "ATTENTE_ACHAT"
            st.balloons()
            st.rerun()

    time.sleep(15)
    st.rerun()
