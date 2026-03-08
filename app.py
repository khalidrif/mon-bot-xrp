import streamlit as st
import ccxt
import json, os, time

st.set_page_config(page_title="Bots Snowball XRP/USDC", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

# ----------------------------------------------------
# SAVE / LOAD
# ----------------------------------------------------
def load_bots():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return []

def save_bots():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)


# ----------------------------------------------------
# INIT SESSION
# ----------------------------------------------------
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

if "last_run" not in st.session_state:
    st.session_state.last_run = 0


# ----------------------------------------------------
# CONNECT KRAKEN
# ----------------------------------------------------
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True
    })
except:
    st.error("Erreur API Kraken.")
    st.stop()


# ----------------------------------------------------
# PRICE XRP/USDC
# ----------------------------------------------------
def get_price():
    try:
        return exchange.fetch_ticker("XRP/USDC")["last"]
    except:
        return None

prix = get_price()

st.title("❄️ Snowball XRP/USDC — Version Stable Final")

if prix is None:
    st.error("Impossible de récupérer le prix XRP/USDC.")
    st.stop()

st.metric("Prix XRP/USDC", f"{prix:.4f}")


# ----------------------------------------------------
# BALANCES
# ----------------------------------------------------
try:
    bal = exchange.fetch_balance()
    usdc_balance = bal["free"].get("USDC", 0.0)
    xrp_balance = bal["free"].get("XRP", 0.0)
except:
    usdc_balance = 0
    xrp_balance = 0

st.metric("USDC disponible", f"{usdc_balance:.4f}")
st.metric("XRP disponible", f"{xrp_balance:.4f}")


# ----------------------------------------------------
# AJOUTER BOT
# ----------------------------------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "OFF",   # OFF ⚫, BUY 🟢, SELL 🔴
        "usdc": 20.0,    # Achat MARKET → jamais partiel → bon pour snowball
        "buy": prix * 0.99,
        "sell": prix * 1.01,
        "entry": None,
        "gain": 0.0,
        "cycles": 0
    })
    save_bots()
    st.rerun()


# ----------------------------------------------------
# AFFICHAGE DES BOTS
# ----------------------------------------------------
for i, bot in enumerate(st.session_state.bots):

    col0, colU, col1, col2, col3, col4, col5, col6 = st.columns([1,2,3,3,3,3,2,1])

    # Pastille d’état
    if bot["mode"] == "OFF":
        col0.write("⚫")
    elif bot["mode"] == "BUY":
        col0.write("🟢")
    else:
        col0.write("🔴")

    # USDC du bot
    bot["usdc"] = colU.number_input(
        "USDC",
        min_value=5.0,
        value=float(bot["usdc"]),
        step=1.0,
        key=f"u{i}"
    )

    # BUY TRIGGER
    bot["buy"] = col1.number_input(
        "Achat si ≤",
        value=float(bot["buy"]),
        format="%.4f",
        key=f"b{i}"
    )

    # SELL LIMIT
    bot["sell"] = col2.number_input(
        "Vente LIMIT ≥",
        value=float(bot["sell"]),
        format="%.4f",
        key=f"s{i}"
    )

    col3.metric("Gain", f"{bot['gain']:.4f}")
    col4.metric("Cycles", bot["cycles"])

    # Start/Stop
    if bot["enabled"]:
        if col5.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "OFF"
            bot["entry"] = None
            save_bots()
            st.rerun()
    else:
        if col5.button("Start", key=f"start{i}"):
            bot["enabled"] = True
            bot["mode"] = "BUY"
            save_bots()
            st.rerun()

    # DELETE BOT
    if col6.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()


# ----------------------------------------------------
# LOGIQUE TRADING — NO REFRESH SPAM
# ----------------------------------------------------
now = time.time()
if now - st.session_state.last_run > 2:

    st.session_state.last_run = now
    prix = get_price()

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        # -----------------------------------------
        # MODE BUY → MARKET
        # -----------------------------------------
        if bot["mode"] == "BUY" and prix <= bot["buy"]:

            qty = round(bot["usdc"] / prix, 6)

            if qty < 5:
                st.warning(f"Bot {i}: Achat impossible (< 5 XRP). Augmente USDC.")
                continue

            try:
                order = exchange.create_market_buy_order("XRP/USDC", qty)
            except Exception as e:
                st.error(f"Erreur BUY MARKET : {e}")
                continue

            filled = order.get("filled", 0)

            # SÉCURITÉ : toujours vérifier après frais
            if filled < 5:
                st.warning(f"Bot {i}: Achat trop faible ({filled} XRP). Annulé.")
                continue

            bot["entry"] = prix
            bot["mode"] = "SELL"
            save_bots()

        # -----------------------------------------
        # MODE SELL → LIMIT
        # -----------------------------------------
        if bot["mode"] == "SELL":

            # VENDRE EXCLUSIVEMENT LE XRP RÉEL DANS LE COMPTE
            bal = exchange.fetch_balance()
            sell_qty = round(bal["free"].get("XRP", 0.0), 6)

            if sell_qty < 5:
                continue  # trop petit, attendre

            try:
                order = exchange.create_limit_sell_order("XRP/USDC", sell_qty, bot["sell"])
                order_id = order["id"]
            except Exception as e:
                st.error(f"Erreur SELL LIMIT : {e}")
                continue

            # Vérifier si vendu
            try:
                o = exchange.fetch_order(order_id, "XRP/USDC")
                if o["status"] == "closed":

                    # Gain réel
                    gain = (bot["sell"] - bot["entry"]) * sell_qty
                    bot["gain"] += gain
                    bot["cycles"] += 1

                    # Reset cycle
                    bot["entry"] = None
                    bot["mode"] = "BUY"
                    save_bots()

            except:
                pass

save_bots()
