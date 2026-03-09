import streamlit as st
import ccxt
import time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Infinite Bot", layout="wide")

@st.cache_resource
def get_exchange():
    # Configuration stable pour éviter l'erreur InvalidNonce
    ex = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': 'milliseconds'}
    })
    ex.load_markets()
    return ex

exchange = get_exchange()
symbol = "XRP/USDC"

# --- MÉMOIRE ---
if 'actif' not in st.session_state: st.session_state.actif = False
# Compteur d'achats pour permettre d'acheter "plusieurs fois"
if 'nb_achats' not in st.session_state: st.session_state.nb_achats = 0

# --- SIDEBAR (RÉGLAGES) ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    p_achat = st.number_input("Cible ACHAT (LIMIT)", value=1.3500, format="%.4f")
    p_vente = st.number_input("Cible VENTE (LIMIT)", value=1.3800, format="%.4f")
    mise_usdc = st.number_input("Mise par achat (USDC)", min_value=10.0, value=20.0)
    limite_max = st.number_input("Nombre d'achats max", value=50)
    
    st.divider()
    st.info(f"Achats effectués : **{st.session_state.nb_achats} / {limite_max}**")
    if st.button("🔄 Réinitialiser Compteur"):
        st.session_state.nb_achats = 0
        st.rerun()

# --- RÉCUPÉRATION DES DONNÉES ---
st.title("🤖 XRP Infinite Bot - Multi-Achat")

try:
    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    
    time.sleep(1) # Sécurité Nonce
    
    bal = exchange.fetch_balance()
    usdc_bal = bal['free'].get('USDC', 0.0)
    xrp_bal = bal['free'].get('XRP', 0.0)

    # --- AFFICHAGE CENTRAL (Les 3 colonnes) ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Prix XRP Actuel", f"{current_price:.4f} USDC")
    col2.metric("📉 Cible ACHAT", f"{p_achat:.4f}", delta=round(current_price - p_achat, 4), delta_color="inverse")
    col3.metric("💰 Cible VENTE", f"{p_vente:.4f}", delta=round(current_price - p_vente, 4))

    st.write(f"💼 **Portefeuille** : {usdc_bal:.2f} USDC | {xrp_bal:.2f} XRP")
    st.divider()

except ccxt.InvalidNonce:
    st.warning("⚠️ Synchronisation Kraken... Patientez.")
    time.sleep(5)
    st.rerun()
except Exception as e:
    st.error(f"Erreur : {e}")
    st.stop()

# --- BOUTONS ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LE BOT", type="primary", use_container_width=True):
    st.session_state.actif = True
if c2.button("🛑 ARRÊTER LE BOT", use_container_width=True):
    st.session_state.actif = False

# --- LOGIQUE DE TRADING ---
if st.session_state.actif:
    try:
        # 1. LOGIQUE D'ACHAT (S'exécute plusieurs fois)
        if current_price <= p_achat and st.session_state.nb_achats < limite_max:
            if usdc_bal >= mise_usdc:
                st.warning(f"⚡ ACHAT n°{st.session_state.nb_achats + 1} à {p_achat}")
                
                q = float(exchange.amount_to_precision(symbol, mise_usdc / p_achat))
                p = float(exchange.price_to_precision(symbol, p_achat))
                
                exchange.create_limit_buy_order(symbol, q, p)
                
                st.session_state.nb_achats += 1 # On augmente le nombre d'achats
                st.success("✅ Ordre d'achat placé !")
                time.sleep(5)
                st.rerun()

        # 2. LOGIQUE DE VENTE (Revend tout le stock accumulé)
        elif current_price >= p_vente and xrp_bal > 1:
            st.info(f"💰 Objectif atteint ! Vente de {xrp_bal:.2f} XRP")
            
            q_v = float(exchange.amount_to_precision(symbol, xrp_bal * 0.995))
            p_v = float(exchange.price_to_precision(symbol, p_vente))
            
            exchange.create_limit_sell_order(symbol, q_v, p_v)
            
            st.session_state.nb_achats = 0 # On remet à zéro après la vente totale
            st.balloons()
            time.sleep(10)
            st.rerun()

        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur d'exécution : {e}")
        time.sleep(10)
        st.rerun()
