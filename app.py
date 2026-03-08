import streamlit as st
import ccxt
import json, os, time

st.set_page_config(page_title="Bots Snowball", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

# ---------------------------
# Save / Load
# ---------------------------
def load_bots():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return []

def save_bots():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)

# Init session
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

if "last_run" not in st.session_state:
    st.session_state.last_run = 0

# ---------------------------
# Kraken
# ---------------------------
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True
    })
except:
    st.error("Erreur API Kraken")
    st.stop()

# ---------------------------
# Prix
# ---------------------------
def get_price():
    try:
        return exchange.fetch_ticker("XRP/USD")["last"]
    except:
        return None

prix = get_price()

st.title("❄️ Snowball XRP (Ultra Stable)")
if prix:
    st.metric("Prix XRP", f"{prix:.4f} $")
else:
    st.error("Erreur récupération prix")
    st.stop()

# ---------------------------
# Bouton ajouter bot
# ---------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "BUY",       # BUY = 🟢  SELL = 🔴
        "usdc": 10.0,
        "buy": prix * 0.99,
        "sell": prix * 1.01,
        "entry": None,
        "xrp_qty": 0.0,
        "gain": 0.0,
        "cycles": 0
    })
    save_bots()
    st.rerun()

# ---------------------------
# Affichage des bots
# ---------------------------
for i, bot in enumerate(st.session_state.bots):

    col0, colU, col1, col2, col3, col4, col5 = st.columns([1,2,3,3,3,3,2])

    # Pastille
    col0.write("🟢" if bot["mode"] == "BUY" else "🔴")

    # USDC du bot
    bot["usdc"] = colU.number_input(
        "USDC",
        min_value=1.0,
        value=float(bot["usdc"]),
        key=f"u_{i}"
    )

    # Buy target
    bot["buy"] = col1.number_input(
        "Buy ≤",
        value=float(bot["buy"]),
        format="%.4f",
        key=f"b_{i}"
    )

    # Sell target
    bot["sell"] = col2.number_input(
        "Sell ≥",
        value=float(bot["sell"]),
        format="%.4f",
        key=f"s_{i}"
    )

    # Gain
    col3.metric("Gain", f"{bot['gain']:.4f} $")

    # Cycles
    col4.metric("Cycles", bot["cycles"])

    # Bouton Start/Stop
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

# ---------------------------
# Logique trading (toutes les 2 secondes)
# ---------------------------
now = time.time()
if now - st.session_state.last_run > 2:
    st.session_state.last_run = now

    prix = get_price()

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        # MODE BUY = attendre achat
        if bot["mode"] == "BUY":

            if prix <= bot["buy"]:
                qty = bot["usdc"] / prix

                try:
                    exchange.create_market_buy_order("XRP/USD", qty)
                except Exception as e:
                    st.error(f"Erreur achat : {e}")
                    continue

                bot["entry"] = prix
                bot["xrp_qty"] = qty
                bot["mode"] = "SELL"
                save_bots()

        # MODE SELL = attendre vente
        elif bot["mode"] == "SELL":

            if prix >= bot["sell"]:

                try:
                    exchange.create_market_sell_order("XRP/USD", bot["xrp_qty"])
                except Exception as e:
                    st.error(f"Erreur vente : {e}")
                    continue

                gain = (prix - bot["entry"]) * bot["xrp_qty"]
                bot["gain"] += gain
                bot["cycles"] += 1
                bot["entry"] = None
                bot["mode"] = "BUY"
                save_bots()
