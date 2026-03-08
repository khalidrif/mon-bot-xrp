import streamlit as st
import ccxt
import json, os
from streamlit_autorefresh import st_autorefresh

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Bots Snowball", page_icon="❄️", layout="wide")

SAVE_FILE = "bots_data.json"

# ----------------------------------------------------
# SAUVEGARDE / CHARGEMENT
# ----------------------------------------------------
def save_data():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)

def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return []

# ----------------------------------------------------
# INIT SESSION
# ----------------------------------------------------
if "bots" not in st.session_state:
    st.session_state.bots = load_data()

# ----------------------------------------------------
# KRAKEN
# ----------------------------------------------------
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True,
    })
except:
    st.error("Erreur API Kraken")
    st.stop()

st_autorefresh(interval=7000, key="refresh")

# ----------------------------------------------------
# PRIX & SOLDES
# ----------------------------------------------------
try:
    ticker = exchange.fetch_ticker("XRP/USD")
    prix = ticker["last"]

    bal = exchange.fetch_balance()
    usd_total = next((bal["total"][x] for x in ["USDC","USD","ZUSD"] if x in bal["total"]),0)
    xrp_total = bal["total"].get("XRP", 0)

except:
    st.error("Erreur Kraken")
    st.stop()

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
st.title("❄️ Bots Snowball XRP")
st.metric("Prix XRP", f"{prix:.4f} $")

# ----------------------------------------------------
# BOUTON AJOUT BOT
# ----------------------------------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "BUY",           # BUY → pastille verte / SELL → rouge
        "usdc": 10,              # montant USDC utilisé par ce bot
        "buy": prix * 0.99,
        "sell": prix * 1.01,
        "entry": None,
        "gain": 0.0,
        "cycles": 0
    })
    save_data()
    st.rerun()

# ----------------------------------------------------
# AFFICHAGE DES BOTS
# ----------------------------------------------------
for i, bot in enumerate(st.session_state.bots):

    col0, colU, col1, col2, col3, col4, col5 = st.columns([1,2,3,3,3,3,2])

    # Pastille
    if bot["mode"] == "BUY":
        col0.markdown("🟢")
    else:
        col0.markdown("🔴")

    # Montant USDC
    bot["usdc"] = colU.number_input(
        "USDC",
        min_value=1.0,
        value=float(bot["usdc"]),
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

    # Gain
    col3.metric("Gain", f"{bot['gain']:.4f} $")

    # Cycles
    col4.metric("Cycles", bot["cycles"])

    # Bouton Start / Stop
    if bot["enabled"]:
        if col5.button("Stop", key=f"stop_{i}"):
            bot["enabled"] = False
            bot["entry"] = None
            save_data()
            st.rerun()
    else:
        if col5.button("Start", key=f"start_{i}"):
            bot["enabled"] = True
            bot["mode"] = "BUY"
            save_data()
            st.rerun()

# ----------------------------------------------------
# LOGIQUE TRADING SNOWBALL
# ----------------------------------------------------
for bot in st.session_state.bots:

    if not bot["enabled"]:
        continue

    # Mode BUY (🟢)
    if bot["mode"] == "BUY":

        if prix <= bot["buy"] and bot["usdc"] > 1:

            qty = (bot["usdc"] - 1) / prix

            exchange.create_market_buy_order("XRP/USD", qty)

            bot["entry"] = prix
            bot["mode"] = "SELL"   # passe en mode vente
            save_data()
            st.rerun()

    # Mode SELL (🔴)
    elif bot["mode"] == "SELL":

        if prix >= bot["sell"] and xrp_total > 1:

            exchange.create_market_sell_order("XRP/USD", xrp_total)

            gain = (prix - bot["entry"]) * xrp_total
            bot["gain"] += gain
            bot["cycles"] += 1
            bot["entry"] = None
            bot["mode"] = "BUY"    # recommence cycle

            save_data()
            st.rerun()

# ----------------------------------------------------
# SAUVER À CHAQUE CHANGEMENT
# ----------------------------------------------------
save_data()
