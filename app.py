import streamlit as st
import ccxt
import time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Infinite Bot", layout="wide")

@st.cache_resource
def get_exchange():
    # Configuration spécifique pour éviter l'erreur InvalidNonce
    ex = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {
            'nonce': 'milliseconds' # Utilise le temps précis pour éviter les conflits
        }
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
    p_achat = st.number_input("Cible ACHAT (LIMIT)", value=1.3500, format="%.4f")
    p_vente = st.number_input("Cible VENTE (LIMIT)", value=1.3800, format="%.4f")
    mise_usdc = st.number_input("Mise (USDC)", min_value=10.0, value=20.0)
    
    st.divider()
    st.info(f"Prochaine action : **{st.session_state.etape}**")
    if st.button("🔄 Reset Bot à l'achat"):
        st.session_state.etape = "ATTENTE_ACHAT"
        st.rerun()

# --- RÉCUPÉRATION DES DONNÉES (AVEC SÉCURITÉ NONCE) ---
st.title("🤖 XRP Infinite Bot")

try:
    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    
    # Petite pause pour ne pas saturer le Nonce de Kraken
    time.sleep(1)
    
    bal = exchange.fetch_balance()
    usdc_bal = bal['free'].get('USDC', 0.0)
    xrp_bal = bal['free'].get('XRP', 0.0)

    # --- AFFICHAGE CENTRAL ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Prix XRP Actuel", f"{current_price:.4f} USDC")
    col2.metric("📉 Cible ACHAT", f"{p_achat:.4f}", delta=round(current_price - p_achat, 4), delta_color="inverse")
    col3.metric("💰 Cible VENTE", f"{p_vente:.4f}", delta=round(current_price - p_vente, 4))

    st.write(f"💼 **Portefeuille** : {usdc_bal:.2f} USDC | {xrp_bal:.2f} XRP")
    st.divider()

except ccxt.InvalidNonce:
    st.warning("⚠️ Problème de synchronisation Kraken (Nonce). On réessaie...")
    time.sleep(5)
    st.rerun()
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# --- BOUTONS DE CONTRÔLE ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LE BOT", type="primary", use_container_width=True):
    st.session_state.actif = True
if c2.button("🛑 ARRÊTER LE BOT", use_container_width=True):
    st.session_state.actif = False

# --- LOGIQUE DE TRADING ---
if st.session_state.actif:
    try:
        # 1. LOGIQUE D'ACHAT
        if st.session_state.etape == "ATTENTE_ACHAT" and current_price <= p_achat:
            if usdc_bal >= mise_usdc:
                st.warning(f"⚡ Envoi ORDRE ACHAT : {p_achat} USDC")
                q = float(exchange.amount_to_precision(symbol, mise_usdc / p_achat))
                p = float(exchange.price_to_precision(symbol, p_achat))
                
                exchange.create_limit_buy_order(symbol, q, p)
                st.session_state.etape = "ATTENTE_VENTE"
                st.success("✅ Achat placé ! Passage en mode VENTE.")
                time.sleep(5)
                st.rerun()
            else:
                st.error("Solde USDC insuffisant.")

        # 2. LOGIQUE DE VENTE
        elif st.session_state.etape == "ATTENTE_VENTE" and current_price >= p_vente:
            if xrp_bal > 1:
                st.info(f"💰 Envoi ORDRE VENTE : {p_vente} USDC")
                q_v = float(exchange.amount_to_precision(symbol, xrp_bal * 0.995))
                p_v = float(exchange.price_to_precision(symbol, p_vente))
                
                exchange.create_limit_sell_order(symbol, q_v, p_v)
                st.session_state.etape = "ATTENTE_ACHAT"
                st.balloons()
                time.sleep(10)
                st.rerun()

        # Rafraîchissement automatique toutes les 20 secondes
        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.error(f"⚠️ Erreur durant l'exécution : {e}")
        time.sleep(10)
        st.rerun()
else:
    st.info("Le bot est en veille. Appuyez sur Démarrer.")
