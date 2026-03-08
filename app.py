import streamlit as st
import ccxt
import json, os, time
import math

st.set_page_config(page_title="Bots Snowball LIMIT XRP/USDC", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"


# ---------------------------------------------
# SAVE / LOAD
# ---------------------------------------------
def load_bots():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return []

def save_bots():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)


# ---------------------------------------------
# SESSION INIT
# ---------------------------------------------
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

if "last_run" not in st.session_state:
    st.session_state.last_run = 0


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


# ---------------------------------------------
# GET PRICE XRP/USDC
# ---------------------------------------------
def get_price():
    try:
        return exchange.fetch_ticker("XRP/USDC")["last"]
    except:
        return None


prix = get_price()

st.title("❄️ Snowball XRP/USDC – LIMIT Orders")

if prix:
    st.metric("Prix XRP/USDC", f"{prix:.4f}")
else:
    st.error("Erreur récupération prix")
    st.stop()


# ---------------------------------------------
# Solde USDC Kraken
# ---------------------------------------------
try:
    bal = exchange.fetch_balance()
    usdc_balance = bal["free"].get("USDC", 0)
except:
    usdc_balance = 0

st.metric("USDC Kraken Disponible", f"{usdc_balance:.4f}")


# ---------------------------------------------
# Bouton ajouter bot
# ---------------------------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "OFF",       # OFF⚫ , BUY🟢 , SELL🔴
        "usdc": 10.0,
        "buy": round(prix * 0.99, 4),
        "sell": round(prix * 1.01, 4),
        "entry": None,
        "xrp_qty": 0.0,
        "gain": 0.0,
        "cycles": 0,
        "order_id": None
    })
    save_bots()
    st.rerun()


# ---------------------------------------------
# AFFICHAGE DES BOTS
# ---------------------------------------------
for i, bot in enumerate(st.session_state.bots):

    col0, colU, col1, col2, col3, col4, col5, col6 = st.columns([1,2,3,3,3,3,2,1])

    # Pastille
    if bot["mode"] == "OFF":
        col0.write("⚫")
    elif bot["mode"] == "BUY":
        col0.write("🟢")
    else:
        col0.write("🔴")

    # Montant USDC du bot
    bot["usdc"] = colU.number_input(
        "USDC",
        min_value=1.0,
        value=float(bot["usdc"]),
        key=f"u{i}"
    )

    # Buy LIMIT
    bot["buy"] = col1.number_input(
        "Buy LIMIT ≤",
        value=float(bot["buy"]),
        format="%.4f",
        key=f"b{i}"
    )

    # Sell LIMIT
    bot["sell"] = col2.number_input(
        "Sell LIMIT ≥",
        value=float(bot["sell"]),
        format="%.4f",
        key=f"s{i}"
    )

    # Gain total
    col3.metric("Gain", f"{bot['gain']:.4f} $")

    # Cycles snowball
    col4.metric("Cycles", bot["cycles"])

    # Start / Stop
    if bot["enabled"]:
        if col5.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "OFF"
            bot["entry"] = None
            bot["order_id"] = None
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


# ---------------------------------------------
# LOGIQUE TRADING LIMIT (toutes les 2s)
# ---------------------------------------------
now = time.time()
if now - st.session_state.last_run > 2:
    st.session_state.last_run = now

    prix = get_price()
    if not prix:
        st.stop()

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        # -----------------------------------------
        # MODE BUY (🟢 LIMIT)
        # -----------------------------------------
        if bot["mode"] == "BUY":

            # XRP achetés = USDC / prix LIMIT
            qty = round(bot["usdc"] / bot["buy"], 6)

            try:
                order = exchange.create_limit_buy_order("XRP/USDC", qty, bot["buy"])
                bot["order_id"] = order["id"]
            except Exception as e:
                st.error(f"Erreur BUY LIMIT : {e}")
                continue

            # Vérifier exécution
            try:
                o = exchange.fetch_order(bot["order_id"], "XRP/USDC")
                if o["status"] == "closed":

                    bot["entry"] = bot["buy"]
                    bot["xrp_qty"] = qty
                    bot["mode"] = "SELL"
                    bot["order_id"] = None
                    save_bots()

            except:
                pass

        # -----------------------------------------
        # MODE SELL (🔴 LIMIT)
        # -----------------------------------------
        elif bot["mode"] == "SELL":

            # Vérifier solde réel pour éviter erreurs
            try:
                bal = exchange.fetch_balance()
                xrp_balance = bal["free"].get("XRP", 0)
            except:
                xrp_balance = 0

            sell_qty = min(bot["xrp_qty"], xrp_balance)
            sell_qty = round(sell_qty, 6)

            if sell_qty <= 0:
                continue

            try:
                order = exchange.create_limit_sell_order("XRP/USDC", sell_qty, bot["sell"])
                bot["order_id"] = order["id"]
            except Exception as e:
                st.error(f"Erreur SELL LIMIT : {e}")
                continue

            # Vérifier exécution
            try:
                o = exchange.fetch_order(bot["order_id"], "XRP/USDC")
                if o["status"] == "closed":

                    # calcul gain
                    gain = (bot["sell"] - bot["entry"]) * sell_qty
                    bot["gain"] += gain
                    bot["cycles"] += 1

                    # reset pour snowball
                    bot["entry"] = None
                    bot["order_id"] = None
                    bot["mode"] = "BUY"
                    save_bots()

            except:
                pass


save_bots()
