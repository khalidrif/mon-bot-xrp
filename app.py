import streamlit as st
import ccxt
from streamlit_autorefresh import st_autorefresh

# --- CONFIG GLOBAL ---
st.set_page_config(page_title="Kraken XRP Snowball REAL", page_icon="🐙", layout="wide")

# --- CONNEXION KRAKEN ---
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
except Exception:
    st.error("⚠️ Erreur : Clés API Kraken manquantes dans les Secrets Streamlit.")
    st.stop()

# --- RAFRAICHISSEMENT AUTO ---
st_autorefresh(interval=10000, key="bot_refresh")

# --- MEMOIRE SESSION ---
if "bot_status" not in st.session_state:
    st.session_state.bot_status = "VEILLE"
if "targets" not in st.session_state:
    st.session_state.targets = {"buy": 0.0, "sell": 0.0}

# --- RÉCUPÉRATION DONNÉES ---
try:
    ticker = exchange.fetch_ticker('XRP/USD')
    prix_actuel = ticker['last']

    balance = exchange.fetch_balance()

    # Recherche multi-symbole : USDC, USD, ZUSD
    solde_usd = 0.0
    for symbol in ["USDC", "USD", "ZUSD"]:
        if symbol in balance['total']:
            solde_usd = balance['total'][symbol]
            break

    solde_xrp = balance['total'].get('XRP', 0.0)

except Exception as e:
    st.warning(f"Erreur Kraken : {e}")
    st.stop()

# --- DASHBOARD ---
st.title("🐙 Kraken XRP Auto-Snowball (MODE RÉEL)")

c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP", f"{prix_actuel:.4f} $")
c2.metric("Solde USD", f"{round(solde_usd, 2)} $")
c3.metric("Solde XRP", f"{round(solde_xrp, 2)}")

st.info(f"État du Bot : **{st.session_state.bot_status}**")

# --- PARAMÉTRAGE ---
with st.container(border=True):
    st.subheader("❄️ Paramétrer le cycle")

    col_a, col_b = st.columns(2)
    buy_target = col_a.number_input("Acheter TOUT si prix <= ", value=float(prix_actuel * 0.998), format="%.4f")
    sell_target = col_b.number_input("Vendre TOUT si prix >= ", value=float(prix_actuel * 1.01), format="%.4f")

    if st.button("🚀 ACTIVER LE TRADING RÉEL", type="primary", use_container_width=True):
        st.session_state.targets["buy"] = buy_target
        st.session_state.targets["sell"] = sell_target
        st.session_state.bot_status = "ATTENTE_ACHAT"
        st.rerun()

# --- TRADING LIVE ---
try:

    if st.session_state.bot_status == "ATTENTE_ACHAT":
        if prix_actuel <= st.session_state.targets["buy"] and solde_usd > 5:

            quantite = max((solde_usd - 1) / prix_actuel, 0)

            if quantite < 1:
                st.warning("Pas assez de fonds pour acheter au moins 1 XRP")
            else:
                order = exchange.create_market_buy_order('XRP/USD', quantite)
                st.session_state.bot_status = "EN_POSITION"
                st.success(f"✅ Achat exécuté : {quantite:.2f} XRP")
                st.rerun()

    elif st.session_state.bot_status == "EN_POSITION":
        if prix_actuel >= st.session_state.targets["sell"] and solde_xrp > 1:

            order = exchange.create_market_sell_order('XRP/USD', solde_xrp)
            st.session_state.bot_status = "VEILLE"
            st.balloons()
            st.success(f"💰 Vente exécutée : {solde_xrp:.2f} XRP")
            st.rerun()

except Exception as e:
    st.error(f"Erreur Trade : {e}")

# --- STOP ---
if st.button("🛑 ARRÊTER LE BOT"):
    st.session_state.bot_status = "VEILLE"
    st.session_state.targets = {"buy": 0.0, "sell": 0.0}
    st.rerun()
