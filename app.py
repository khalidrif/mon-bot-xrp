import streamlit as st
import ccxt
import json, os, time
import math

st.set_page_config(page_title="Bots Snowball LIMIT XRP/USDC", page_icon="❄️", layout="wide")

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


# ---------------------------
# SESSION INIT
# ---------------------------
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

if "last_run" not in st.session_state:
    st.session_state.last_run = 0


# ---------------------------
# CONNECT KRAKEN
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
# GET PRICE XRP/USDC
# ---------------------------
def get_price():
    try:
        return exchange.fetch_ticker("XRP/USDC")["last"]
    except:
        return None

prix = get_price()

st.title("❄️ Snowball XRP/USDC – LIMIT Orders (avec minimum 5 XRP)")

if prix:
    st.metric("Prix XRP/USDC", f"{prix:.4f}")
else:
    st.error("Erreur récupération prix")
    st.stop()


# ---------------------------
# Solde USDC Kraken
# ---------------------------
try:
    bal = exchange.fetch_balance()
    usdc_balance = bal["free"].get("USDC", 0.0)
    xrp_balance = bal["free"].get("XRP", 0.0)
except:
    usdc_balance = 0
    xrp_balance = 0

st.metric("USDC Kraken Disponible", f"{usdc_balance:.4f}")
st.metric("XRP Kraken Disponible", f"{xrp_balance:.4f}")


# ---------------------------
# AJOUT BOT
# ---------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "OFF",     # OFF⚫ , BUY🟢 , SELL🔴
        "usdc": 15.0,      # 15 USDC = ~11 XRP minimum
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


# ---------------------------
# AFFICHAGE DES BOTS
# ---------------------------
for i, bot in enumerate(st.session_state.bots):

    col0, colU, col1, col2, col3, col4, col5, col6 = st.columns([1,2,3,3,3,3,2,1])

    if bot["mode"] == "OFF":
        col0.write("⚫")
    elif bot["mode"] == "BUY":
        col0.write("🟢")
    else:
        col0.write("🔴")

    bot["usdc"] = colU.number_input(
        "USDC",
        min_value=5.0,
        value=float(bot["usdc"]),
        step=1.0,
        key=f"u{i}"
    )

    bot["buy"] = col1.number_input(
        "BUY LIMIT ≤",
        value=float(bot["buy"]),
        format="%.4f",
        key=f"b{i}"
    )

    bot["sell"] = col2.number_input(
        "SELL LIMIT ≥",
        value=float(bot["sell"]),
        format="%.4f",
        key=f"s{i}"
    )

    col3.metric("Gain", f"{bot['gain']:.4f} $")
    col4.metric("Cycles", bot["cycles"])

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

    # SUPPRIMER BOT
    if col6.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()


# ---------------------------
# LOGIQUE LIMIT AVEC MINIMUM 5 XRP
# ---------------------------
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

            qty = round(bot["usdc"] / bot["buy"], 6)

            # Doit être >= 5 XRP
            if qty < 5:
                st.warning(f"Bot nécessite minimum 5 XRP (augmenter USDC). Actuel : {qty}")
                continue

            try:
                order = exchange.create_limit_buy_order("XRP/USDC", qty, bot["buy"])
                bot["order_id"] = order["id"]
            except Exception as e:
                st.error(f"Erreur BUY LIMIT : {e}")
                continue

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

            try:
                bal = exchange.fetch_balance()
                xrp_balance = bal["free"].get("XRP", 0.0)
            except:
                xrp_balance = 0.0

            sell_qty = round(min(bot["xrp_qty"], xrp_balance), 6)

            # Minimum 5 XRP pour vendre sur Kraken
            if sell_qty < 5:
                st.warning(f"Bot ne peut pas vendre ({sell_qty} XRP < 5 min)")
                continue

            try:
                order = exchange.create_limit_sell_order("XRP/USDC", sell_qty, bot["sell"])
                bot["order_id"] = order["id"]
            except Exception as e:
                st.error(f"Erreur SELL LIMIT : {e}")
                continue

            try:
                o = exchange.fetch_order(bot["order_id"], "XRP/USDC")
                if o["status"] == "closed":

                    gain = (bot["sell"] - bot["entry"]) * sell_qty
                    bot["gain"] += gain
                    bot["cycles"] += 1

                    bot["entry"] = None
                    bot["order_id"] = None
                    bot["mode"] = "BUY"

                    save_bots()

            except:
                pass


save_bots()
