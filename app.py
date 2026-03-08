import streamlit as st
import ccxt
import json, os, time

st.set_page_config(page_title="Bots Snowball XRP/USDC", page_icon="❄️", layout="wide")

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
# Prix XRP/USDC
# ---------------------------
def get_price():
    try:
        return exchange.fetch_ticker("XRP/USDC")["last"]
    except:
        return None

prix = get_price()

st.title("❄️ Snowball XRP/USDC – Ultra Stable")

if prix:
    st.metric("Prix XRP/USDC", f"{prix:.4f}")
else:
    st.error("Erreur récupération prix")
    st.stop()

# ---------------------------
# Solde USDC réel Kraken
# ---------------------------
try:
    bal = exchange.fetch_balance()
    usdc_balance = bal["total"].get("USDC", 0)
except:
    usdc_balance = 0

st.metric("USDC Kraken Disponible", f"{usdc_balance:.4f}")

# ---------------------------
# Ajouter bot
# ---------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "BUY",       # BUY = 🟢 , SELL = 🔴
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

    # Montant USDC utilisé par ce bot
    bot["usdc"] = colU.number_input(
        "USDC",
        min_value=1.0,
        value=float(bot["usdc"]),
        key=f"u{i}"
    )

    # Buy limit
    bot["buy"] = col1.number_input(
        "Buy ≤",
        value=float(bot["buy"]),
        format="%.4f",
        key=f"b{i}"
    )

    # Sell limit
    bot["sell"] = col2.number_input(
        "Sell ≥",
        value=float(bot["sell"]),
        format="%.4f",
        key=f"s{i}"
    )

    # Gain
    col3.metric("Gain", f"{bot['gain']:.4f} $")

    # Cycles snowball
    col4.metric("Cycles", bot["cycles"])

    # Start / Stop
    if bot["enabled"]:
        if col5.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["entry"] = None
            bot["mode"] = "BUY"
            save_bots()
            st.rerun()
    else:
        if col5.button("Start", key=f"start{i}"):
            bot["enabled"] = True
            bot["mode"] = "BUY"
            save_bots()
            st.rerun()

# ---------------------------
# LOGIQUE SNOWBALL
# ---------------------------
now = time.time()
if now - st.session_state.last_run > 2:  # toutes les 2s
    st.session_state.last_run = now

    prix = get_price()

    if prix:

        for bot in st.session_state.bots:

            if not bot["enabled"]:
                continue

            # MODE BUY (🟢)
            if bot["mode"] == "BUY":

                if prix <= bot["buy"]:

                    qty = bot["usdc"] / prix

                    try:
                        exchange.create_market_buy_order("XRP/USDC", qty)
                    except Exception as e:
                        st.error(f"Erreur achat bot : {e}")
                        continue

                    bot["entry"] = prix
                    bot["xrp_qty"] = qty
                    bot["mode"] = "SELL"
                    save_bots()

            # MODE SELL (🔴)
            elif bot["mode"] == "SELL":

                if prix >= bot["sell"]:

                    try:
                        exchange.create_market_sell_order("XRP/USDC", bot["xrp_qty"])
                    except Exception as e:
                        st.error(f"Erreur vente bot : {e}")
                        continue

                    gain = (prix - bot["entry"]) * bot["xrp_qty"]
                    bot["gain"] += gain
                    bot["cycles"] += 1
                    bot["entry"] = None
                    bot["mode"] = "BUY"
                    save_bots()
