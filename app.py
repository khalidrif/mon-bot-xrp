import streamlit as st
import ccxt
import json, os
import time

st.set_page_config(page_title="Bots Snowball", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

# -------------------------------
# SAUVEGARDE
# -------------------------------
def save():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)

def load():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return []

# -------------------------------
# SESSION
# -------------------------------
if "bots" not in st.session_state:
    st.session_state.bots = load()

if "last_check" not in st.session_state:
    st.session_state.last_check = 0

# -------------------------------
# KRAKEN
# -------------------------------
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True
    })
except:
    st.error("Erreur API Kraken")
    st.stop()

# -------------------------------
# FONCTION : GET PRICE
# -------------------------------
@st.cache_data(ttl=2)
def get_price():
    return exchange.fetch_ticker("XRP/USD")["last"]

# -------------------------------
# UI PRINCIPALE
# -------------------------------
st.title("❄️ Snowball XRP – Ultra Stable")

prix = get_price()
st.metric("Prix XRP", f"{prix:.4f}")

# -------------------------------
# AJOUT BOT
# -------------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "BUY",
        "usdc": 10.0,
        "buy": prix * 0.99,
        "sell": prix * 1.01,
        "entry": None,
        "xrp_qty": 0.0,
        "gain": 0.0,
        "cycles": 0
    })
    save()
    st.experimental_rerun()

# -------------------------------
# AFFICHAGE BOTS
# -------------------------------
for i, bot in enumerate(st.session_state.bots):

    col0, colU, col1, col2, col3, col4, col5 = st.columns([1,2,3,3,3,3,2])

    # PASTILLE
    col0.write("🟢" if bot["mode"] == "BUY" else "🔴")

    # MONTANT USDC
    bot["usdc"] = colU.number_input(
        "USDC",
        min_value=1.0,
        value=float(bot["usdc"]),
        key=f"u{i}"
    )

    # BUY
    bot["buy"] = col1.number_input(
        "Buy ≤",
        value=float(bot["buy"]),
        format="%.4f",
        key=f"b{i}"
    )

    # SELL
    bot["sell"] = col2.number_input(
        "Sell ≥",
        value=float(bot["sell"]),
        format="%.4f",
        key=f"s{i}"
    )

    # GAIN
    col3.metric("Gain", f"{bot['gain']:.4f} $")

    # CYCLES
    col4.metric("Cycles", bot["cycles"])

    # START / STOP
    if bot["enabled"]:
        if col5.button("Stop", key=f"x{i}"):
            bot["enabled"] = False
            bot["entry"] = None
            bot["mode"] = "BUY"
            save()
            st.experimental_rerun()
    else:
        if col5.button("Start", key=f"y{i}"):
            bot["enabled"] = True
            bot["mode"] = "BUY"
            save()
            st.experimental_rerun()

# -------------------------------
# LOGIQUE TRADING (légère et rapide)
# -------------------------------
now = time.time()

# Pour éviter spam → vérif toutes les 2 secondes
if now - st.session_state.last_check > 2:
    st.session_state.last_check = now

    prix = get_price()

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        # MODE BUY
        if bot["mode"] == "BUY":

            if prix <= bot["buy"]:

                qty = bot["usdc"] / prix

                try:
                    exchange.create_market_buy_order("XRP/USD", qty)
                except Exception as e:
                    st.error(f"Erreur achat Bot : {e}")
                    continue

                bot["entry"] = prix
                bot["xrp_qty"] = qty
                bot["mode"] = "SELL"
                save()

        # MODE SELL
        elif bot["mode"] == "SELL":

            if prix >= bot["sell"]:

                try:
                    exchange.create_market_sell_order("XRP/USD", bot["xrp_qty"])
                except Exception as e:
                    st.error(f"Erreur vente Bot : {e}")
                    continue

                gain = (prix - bot["entry"]) * bot["xrp_qty"]
                bot["gain"] += gain
                bot["cycles"] += 1
                bot["entry"] = None
                bot["mode"] = "BUY"
                save()

st.success("Bot opérationnel – aucune surcharge ✓")
