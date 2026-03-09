import streamlit as st
import ccxt
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Infinite Bot", layout="wide")
st.title("🤖 Bot XRP - Boucle Infinie (Limit)")

# Connexion sécurisée
@st.cache_resource
def get_exchange():
    ex = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
    })
    ex.load_markets() # Indispensable pour la précision
    return ex

exchange = get_exchange()
symbol = "XRP/USDC"

# --- MÉMOIRE ---
if 'actif' not in st.session_state:
    st.session_state.actif = False
if 'etape' not in st.session_state:
    st.session_state.etape = "ATTENTE_ACHAT"

# --- RÉGLAGES ---
with st.sidebar:
    st.header("⚙️ Stratégie")
    p_achat_cible = st.number_input("Prix ACHAT", value=1.3500, format="%.4f")
    p_vente_cible = st.number_input("Prix VENTE", value=1.3800, format="%.4f")
    mise_usdc = st.number_input("Mise (USDC)", min_value=10.0, value=20.0)
    
    st.divider()
    st.info(f"Prochaine action : **{st.session_state.etape}**")
    if st.button("🔄 Reset à ACHAT"):
        st.session_state.etape = "ATTENTE_ACHAT"
        st.rerun()

# --- BOUTONS ---
c1, c2 = st.columns(2)
if c1.button("🚀 LANCER LA BOUCLE", type="primary", use_container_width=True):
    st.session_state.actif = True
if c2.button("🛑 STOP", use_container_width=True):
    st.session_state.actif = False

# --- LOGIQUE ---
if st.session_state.actif:
    try:
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        bal = exchange.fetch_balance()
        usdc_bal = bal['free'].get('USDC', 0.0)
        xrp_bal = bal['free'].get('XRP', 0.0)

        # Affichage
        st.metric("Prix XRP actuel", f"{current_price:.4f} USDC")
        st.write(f"💰 Portefeuille : **{usdc_bal:.2f} USDC** | **{xrp_bal:.2f} XRP**")

        # 1. LOGIQUE ACHAT
        if st.session_state.etape == "ATTENTE_ACHAT" and current_price <= p_achat_cible:
            if usdc_bal >= mise_usdc:
                # Calcul précis pour Kraken
                p_precis = float(exchange.price_to_precision(symbol, p_achat_cible))
                q_precis = float(exchange.amount_to_precision(symbol, mise_usdc / p_achat_cible))
                
                st.warning(f"⚡ Envoi ORDRE ACHAT : {q_precis} XRP à {p_precis}")
                ordre = exchange.create_limit_buy_order(symbol, q_precis, p_precis)
                
                st.session_state.etape = "ATTENTE_VENTE"
                st.success(f"✅ Ordre Achat Placé ! ID: {ordre['id']}")
                time.sleep(5)
                st.rerun()

        # 2. LOGIQUE VENTE
        elif st.session_state.etape == "ATTENTE_VENTE" and current_price >= p_vente_cible:
            if xrp_bal > 1:
                # Calcul précis
                p_precis_v = float(exchange.price_to_precision(symbol, p_vente_cible))
                q_precis_v = float(exchange.amount_to_precision(symbol, xrp_bal * 0.995)) # Marge de frais
                
                st.info(f"💰 Envoi ORDRE VENTE : {q_precis_v} XRP à {p_precis_v}")
                ordre = exchange.create_limit_sell_order(symbol, q_precis_v, p_precis_v)
                
                st.session_state.etape = "ATTENTE_ACHAT"
                st.balloons()
                time.sleep(10)
                st.rerun()

        time.sleep(15)
        st.rerun()

    except Exception as e:
        st.error(f"⚠️ Erreur : {e}")
        time.sleep(10)
        st.rerun()
