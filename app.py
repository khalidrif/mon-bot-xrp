import streamlit as st
import ccxt
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="Bots Snowball", page_icon="❄️", layout="wide")

st.markdown("""
<style>
.bot-row {
    border: 1px solid #cccccc55;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
    background: #f7f7f7;
}
.status-green {
    color: #1FAA59; font-size: 30px;
}
.status-red {
    color: #B4161B; font-size: 30px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CONNECT KRAKEN
# ---------------------------------------------------
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True,
    })
except:
    st.error("Erreur clé API")
    st.stop()

st_autorefresh(interval=8000, key="refresh")

# ---------------------------------------------------
# SESSION DATA
# ---------------------------------------------------
if "bots" not in st.session_state:
    st.session_state.bots = []

# ---------------------------------------------------
# PRIX + SOLDES
# ---------------------------------------------------
try:
    ticker = exchange.fetch_ticker("XRP/USD")
    prix = ticker["last"]

    bal = exchange.fetch_balance()

    usd = next((bal["total"][s] for s in ["USDC", "USD", "ZUSD"] if s in bal["total"]), 0)
    xrp = bal["total"].get("XRP", 0.0)
except:
    st.error("Erreur connexion Kraken.")
    st.stop()

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.title("❄️ Bots Snowball XRP")

st.metric("Prix XRP", f"{prix:.4f} $")

# ---------------------------------------------------
# BOUTON AJOUT BOT
# ---------------------------------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "buy": prix * 0.99,
        "sell": prix * 1.01,
        "entry": None,
        "gain": 0.0,
        "cycles": 0
    })
    st.rerun()

# ---------------------------------------------------
# AFFICHAGE DES BOTS
# ---------------------------------------------------
for i, bot in enumerate(st.session_state.bots):

    st.markdown("<div class='bot-row'>", unsafe_allow_html=True)

    col0, col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 3, 3, 2])

    # Pastille verte / rouge
    if bot["enabled"]:
        col0.markdown("<div class='status-green'>●</div>", unsafe_allow_html=True)
    else:
        col0.markdown("<div class='status-red'>●</div>", unsafe_allow_html=True)

    # Buy
    bot["buy"] = col1.number_input(
        "Buy ≤",
        value=float(bot["buy"]),
        format="%.4f",
        key=f"buy_{i}"
    )

    # Sell
    bot["sell"] = col2.number_input(
        "Sell ≥",
        value=float(bot["sell"]),
        format="%.4f",
        key=f"sell_{i}"
    )

    # Gain total
    col3.metric("Gain", f"{bot['gain']:.4f} $")

    # Nombre de cycles
    col4.metric("Cycles", bot["cycles"])

    # Bouton ON/OFF
    if bot["enabled"]:
        if col5.button(f"Stop", key=f"stop_{i}"):
            bot["enabled"] = False
            bot["entry"] = None
            st.rerun()
    else:
        if col5.button(f"Start", key=f"start_{i}"):
            bot["enabled"] = True
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# LOGIQUE DE TRADING
# ---------------------------------------------------
for bot in st.session_state.bots:

    if not bot["enabled"]:
        continue

    # ACHAT
    if bot["entry"] is None:
        if prix <= bot["buy"] and usd > 5:
            qty = (usd - 1) / prix
            exchange.create_market_buy_order("XRP/USD", qty)
            bot["entry"] = prix
            st.rerun()

    # VENTE
    else:
        if prix >= bot["sell"] and xrp > 1:
            exchange.create_market_sell_order("XRP/USD", xrp)
            gain = (prix - bot["entry"]) * xrp
            bot["gain"] += gain
            bot["cycles"] += 1
            bot["entry"] = None    # restart snowball
            st.rerun()
