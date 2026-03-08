import streamlit as st
import ccxt
import json, os
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------
# CONFIG
# ---------------------------------------------
st.set_page_config(page_title="Bots Snowball XRP", page_icon="❄️", layout="wide")
SAVE_FILE = "bots.json"

st.markdown("""
<style>
.bot-row {
    border: 1px solid #cccccc55;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
    background: #f4f4f4;
}
.icon {
    font-size: 30px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------
# SAVE / LOAD BOTS
# ---------------------------------------------
def load_bots():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return []

def save_bots():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)

if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

# ---------------------------------------------
# CONNECT KRAKEN
# ---------------------------------------------
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True
    })
except:
    st.error("Erreur API Kraken")
    st.stop()

st_autorefresh(interval=7000, key="refresh")

# ---------------------------------------------
# PRIX & SOLDES KRAKEN
# ---------------------------------------------
try:
    ticker = exchange.fetch_ticker("XRP/USD")
    prix = ticker["last"]

    bal = exchange.fetch_balance()

    usd_kraken = next((bal["total"][x] for x in ["USDC","USD","ZUSD"] if x in bal["total"]), 0)
except Exception as e:
    st.error(f"Erreur Kraken : {e}")
    st.stop()

# ---------------------------------------------
# HEADER
# ---------------------------------------------
st.title("❄️ Bots Snowball XRP")
st.metric("Prix XRP", f"{prix:.4f} $")
st.metric("USDC disponible Kraken", f"{usd_kraken:.2f} $")

# ---------------------------------------------
# AJOUTER UN BOT
# ---------------------------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "BUY",      # BUY = pastille verte, SELL = pastille rouge
        "usdc": 10.0,       # montant du bot
        "buy": prix * 0.99,
        "sell": prix * 1.01,
        "entry": None,
        "xrp_qty": 0.0,
        "gain": 0.0,
        "cycles": 0
    })
    save_bots()
    st.rerun()

# ---------------------------------------------
# AFFICHAGE DES BOTS
# ---------------------------------------------
for i, bot in enumerate(st.session_state.bots):

    st.markdown("<div class='bot-row'>", unsafe_allow_html=True)

    col0, colU, col1, col2, col3, col4, col5 = st.columns([1,2,3,3,3,3,2])

    # Pastille de statut
    if bot["mode"] == "BUY":
        col0.markdown("<span class='icon'>🟢</span>", unsafe_allow_html=True)
    else:
        col0.markdown("<span class='icon'>🔴</span>", unsafe_allow_html=True)

    # Montant utilisé par ce bot
    bot["usdc"] = colU.number_input(
        "USDC",
        value=float(bot["usdc"]),
        min_value=1.0,
        step=1.0,
        key=f"usdc_{i}"
    )

    # Buy target
    bot["buy"] = col1.number_input(
        "Buy ≤",
        value=float(bot["buy"]),
        format="%.4f",
        key=f"buy_{i}"
    )

    # Sell target
    bot["sell"] = col2.number_input(
        "Sell ≥",
        value=float(bot["sell"]),
        format="%.4f",
        key=f"sell_{i}"
    )

    # Gain total
    col3.metric("Gain", f"{bot['gain']:.4f} $")

    # Cycles snowball
    col4.metric("Cycles", bot["cycles"])

    # Bouton START / STOP
    if bot["enabled"]:
        if col5.button("Stop", key=f"stop_{i}"):
            bot["enabled"] = False
            bot["entry"] = None
            bot["mode"] = "BUY"
            save_bots()
            st.rerun()
    else:
        if col5.button("Start", key=f"start_{i}"):
            bot["enabled"] = True
            bot["mode"] = "BUY"
            save_bots()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------
# LOGIQUE TRADING SNOWBALL
# ---------------------------------------------
for bot in st.session_state.bots:

    if not bot["enabled"]:
        continue

    # MODE BUY = 🟢
    if bot["mode"] == "BUY":

        if prix <= bot["buy"] and bot["usdc"] > 1:

            qty = bot["usdc"] / prix

            try:
                exchange.create_market_buy_order("XRP/USD", qty)
            except Exception as e:
                st.error(f"Erreur achat bot : {e}")
                continue

            bot["entry"] = prix
            bot["xrp_qty"] = qty
            bot["mode"] = "SELL"
            save_bots()
            st.rerun()

    # MODE SELL = 🔴
    elif bot["mode"] == "SELL":

        if prix >= bot["sell"]:

            try:
                exchange.create_market_sell_order("XRP/USD", bot["xrp_qty"])
            except Exception as e:
                st.error(f"Erreur vente bot : {e}")
                continue

            gain = (prix - bot["entry"]) * bot["xrp_qty"]
            bot["gain"] += gain
            bot["cycles"] += 1
            bot["entry"] = None
            bot["mode"] = "BUY"

            save_bots()
            st.rerun()

# ---------------------------------------------
# SAUVEGARDE FINALE
# ---------------------------------------------
save_bots()
