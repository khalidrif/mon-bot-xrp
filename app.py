import streamlit as st
import ccxt
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Kraken XRP Snowball REAL", page_icon="🐙", layout="wide")

# --- CONNEXION KRAKEN (Via Secrets) ---
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
except Exception:
    st.error("⚠️ Erreur : Clés API Kraken manquantes dans les Secrets Streamlit.")
    st.stop()

# --- REFRESH AUTO (Toutes les 10 secondes) ---
st_autorefresh(interval=10000, key="bot_loop")

# --- INITIALISATION MÉMOIRE ---
if "bot_status" not in st.session_state:
    st.session_state.bot_status = "VEILLE" # VEILLE, ATTENTE_ACHAT, EN_POSITION
if "targets" not in st.session_state:
    st.session_state.targets = {"buy": 0.0, "sell": 0.0}

# --- RÉCUPÉRATION DES DONNÉES RÉELLES ---
try:
    # 1. Prix XRP en direct
    ticker = exchange.fetch_ticker('XRP/USD')
    prix_actuel = ticker['last']

    # 2. Soldes Réels
    balance = exchange.fetch_balance()
    solde_usdc = balance['total'].get('USDC', balance['total'].get('ZUSD', 0.0))
    solde_xrp = balance['total'].get('XRP', 0.0)
except Exception as e:
    st.warning(f"Erreur de connexion Kraken : {e}")
    prix_actuel = 0.0
    solde_usdc = 0.0

# --- UI : DASHBOARD ---
st.title("🐙 Kraken XRP Auto-Snowball (MODE RÉEL)")

c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP", f"{prix_actuel} $")
c2.metric("Solde USDC", f"{round(solde_usdc, 2)} $")
c3.metric("Solde XRP", f"{round(solde_xrp, 2)}")

st.info(f"État actuel du Bot : **{st.session_state.bot_status}**")

# --- CONFIGURATION DU CYCLE ---
with st.container(border=True):
    st.subheader("❄️ Paramétrer la Boule de Neige")
    col_a, col_b = st.columns(2)
    
    buy_target = col_a.number_input("Acheter TOUT si prix <= ", value=prix_actuel * 0.998, format="%.4f")
    sell_target = col_b.number_input("Vendre TOUT si prix >= ", value=prix_actuel * 1.01, format="%.4f")
    
    if st.button("🚀 ACTIVER LE TRADING RÉEL", use_container_width=True, type="primary"):
        st.session_state.targets["buy"] = buy_target
        st.session_state.targets["sell"] = sell_target
        st.session_state.bot_status = "ATTENTE_ACHAT"
        st.rerun()

# --- LOGIQUE DE TRADING RÉEL ---
if st.session_state.bot_status == "ATTENTE_ACHAT":
    if prix_actuel <= st.session_state.targets["buy"] and solde_usdc > 5:
        try:
            # Calcul quantité (On garde 1$ de marge pour les frais)
            quantite = (solde_usdc - 1) / prix_actuel
            # ORDRE D'ACHAT RÉEL
            exchange.create_market_buy_order('XRP/USD', quantite)
            st.session_state.bot_status = "EN_POSITION"
            st.success(f"✅ ACHAT RÉEL EFFECTUÉ : {quantite} XRP")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur Achat : {e}")

elif st.session_state.bot_status == "EN_POSITION":
    if prix_actuel >= st.session_state.targets["sell"] and solde_xrp > 1:
        try:
            # ORDRE DE VENTE RÉEL
            exchange.create_market_sell_order('XRP/USD', solde_xrp)
            st.session_state.bot_status = "VEILLE"
            st.balloons()
            st.success(f"💰 VENTE RÉELLE EFFECTUÉE : {solde_xrp} XRP")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur Vente : {e}")

# --- ARRÊT D'URGENCE ---
if st.button("🛑 ARRÊTER LE BOT"):
    st.session_state.bot_status = "VEILLE"
    st.rerun()
