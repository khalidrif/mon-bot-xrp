import streamlit as st
import ccxt
from streamlit_autorefresh import st_autorefresh

# ------------------------------------------------------
# CONFIG
# ------------------------------------------------------
st.set_page_config(page_title="Kraken Multi-Bots XRP", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.bot-block {
    padding: 15px;
    border-radius: 10px;
    background: #11111111;
    margin-bottom: 15px;
    border: 1px solid #CCCCCC55;
}
.red-box {
    background:#B4161B;color:white;padding:8px;border-radius:6px;text-align:center;
}
.green-box {
    background:#1FAA59;color:white;padding:8px;border-radius:6px;text-align:center;
}
@media (max-width: 600px) {
    .block-container { padding-left: 0.3rem; padding-right: 0.3rem; }
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------
# CONNEXION KRAKEN
# ------------------------------------------------------
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True,
    })
except:
    st.error("Clés API Kraken manquantes.")
    st.stop()

st_autorefresh(interval=10000, key="refresh")

# ------------------------------------------------------
# SESSION STATE INITIALISATION
# ------------------------------------------------------
if "nb_bots" not in st.session_state:
    st.session_state.nb_bots = 1

if "bots" not in st.session_state:
    st.session_state.bots = {}

# ------------------------------------------------------
# MISE À JOUR NOMBRE DE BOTS
# ------------------------------------------------------
st.sidebar.title("🤖 Gestion des Bots")

nb = st.sidebar.number_input("Nombre total de bots :", min_value=1, max_value=200, step=1)
st.session_state.nb_bots = nb

# Créer automatiquement les bots manquants
for i in range(1, st.session_state.nb_bots + 1):
    key = f"bot{i}"
    if key not in st.session_state.bots:
        st.session_state.bots[key] = {
            "enabled": False,
            "status": "VEILLE",
            "buy": 0.0,
            "sell": 0.0,
            "entry": None,
            "gain": 0.0,
        }

# ------------------------------------------------------
# DONNÉES KRAKEN
# ------------------------------------------------------
try:
    ticker = exchange.fetch_ticker("XRP/USD")
    prix = ticker["last"]

    balance = exchange.fetch_balance()
    usd = next((balance["total"][s] for s in ["USDC", "USD", "ZUSD"] if s in balance["total"]), 0)
    xrp = balance["total"].get("XRP", 0.0)

except Exception as e:
    st.error(f"Erreur Kraken : {e}")
    st.stop()

# ------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------
st.title("🤖 Multi-Bots XRP (Nombre illimité)")

c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP", f"{prix:.4f} $")
c2.metric("USD", f"{usd:.2f} $")
c3.metric("XRP", f"{xrp:.4f}")

# ------------------------------------------------------
# BOUCLE D'AFFICHAGE DES BOTS
# ------------------------------------------------------
for i in range(1, st.session_state.nb_bots + 1):

    bot = st.session_state.bots[f"bot{i}"]

    st.markdown(f"<div class='bot-block'>", unsafe_allow_html=True)

    st.markdown(f"## Bot {i}")

    # Activation du bot
    if bot["enabled"]:
        if st.button(f"🛑 Stop Bot {i}"):
            bot["enabled"] = False
            bot["status"] = "VEILLE"
            st.rerun()
    else:
        if st.button(f"🚀 Activer Bot {i}"):
            bot["enabled"] = True
            bot["status"] = "ATTENTE_ACHAT"
            st.rerun()

    # Paramètres du bot
    col1, col2 = st.columns(2)
    bot["buy"] = col1.number_input(f"Bot {i} - Acheter si prix ≤", value=float(prix*0.99), format="%.4f", key=f"buy_{i}")
    bot["sell"] = col2.number_input(f"Bot {i} - Vendre si prix ≥", value=float(prix*1.01), format="%.4f", key=f"sell_{i}")

    # Fourchette de prix colorée
    if bot["status"] == "EN_POSITION":
        st.markdown(f"<div class='green-box'>Achat ≤ {bot['buy']} | Vente ≥ {bot['sell']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='red-box'>Achat ≤ {bot['buy']} | Vente ≥ {bot['sell']}</div>", unsafe_allow_html=True)

    # Gain
    st.metric("Gain total", f"{bot['gain']:.4f} $")

    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------
# LOGIQUE DE TRADING
# ------------------------------------------------------
for i in range(1, st.session_state.nb_bots + 1):

    bot = st.session_state.bots[f"bot{i}"]

    if not bot["enabled"]:
        continue

    # Achat automatique
    if bot["status"] == "ATTENTE_ACHAT":
        if prix <= bot["buy"] and usd > 5:
            qty = (usd - 1) / prix
            exchange.create_market_buy_order("XRP/USD", qty)
            bot["entry"] = prix
            bot["status"] = "EN_POSITION"
            st.success(f"Bot {i} : ACHAT {qty:.2f} XRP")
            st.rerun()

    # Vente automatique
    if bot["status"] == "EN_POSITION":
        if prix >= bot["sell"] and xrp > 1:
            exchange.create_market_sell_order("XRP/USD", xrp)
            gain = (prix - bot["entry"]) * xrp
            bot["gain"] += gain
            bot["status"] = "ATTENTE_ACHAT"
            st.success(f"Bot {i} : VENTE +{gain:.4f} $")
            st.rerun()
