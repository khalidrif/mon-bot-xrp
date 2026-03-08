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
            bots = json.load(f)
    else:
        return []

    # AUTO-REPAIR for missing keys
    for bot in bots:
        if "enabled" not in bot: bot["enabled"] = False
        if "mode" not in bot: bot["mode"] = "OFF"
        if "usdc" not in bot: bot["usdc"] = 20.0
        if "buy_trigger" not in bot: bot["buy_trigger"] = 0.0
        if "sell_price" not in bot: bot["sell_price"] = 0.0
        if "entry" not in bot: bot["entry"] = None
        if "xrp_qty" not in bot: bot["xrp_qty"] = 0.0
        if "gain" not in bot: bot["gain"] = 0.0
        if "cycles" not in bot: bot["cycles"] = 0

    return bots

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
    st.error("Erreur API Kraken")
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

st.title("❄️ Snowball XRP/USDC – Version Stable & Auto-Fix")

if prix is None:
    st.error("Erreur prix.")
    st.stop()

st.metric("Prix XRP/USDC", f"{prix:.4f}")


# ----------------------------------------------------
# BALANCE
# ----------------------------------------------------
try:
    bal = exchange.fetch_balance()
    usdc_kraken = bal["free"].get("USDC", 0.0)
except:
    usdc_kraken = 0.0

st.metric("USDC Disponible", f"{usdc_kraken:.4f}")


# ----------------------------------------------------
# AJOUT BOT
# ----------------------------------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "OFF",
        "usdc": 20.0,
        "buy_trigger": prix * 0.99,
        "sell_price": prix * 1.01,
        "entry": None,
        "xrp_qty": 0.0,
        "gain": 0.0,
        "cycles": 0
    })
    save_bots()
    st.rerun()


# ----------------------------------------------------
# AFFICHAGE DES BOTS
# ----------------------------------------------------
for i, bot in enumerate(st.session_state.bots):

    # Auto-fix in UI
    bot.setdefault("enabled", False)
    bot.setdefault("mode", "OFF")
    bot.setdefault("usdc", 20.0)
    bot.setdefault("buy_trigger", prix * 0.99)
    bot.setdefault("sell_price", prix * 1.01)
    bot.setdefault("entry", None)
    bot.setdefault("xrp_qty", 0.0)
    bot.setdefault("gain", 0.0)
    bot.setdefault("cycles", 0)

    col0, colU, col1, col2, col3, col4, col5, col6 = st.columns([1,2,3,3,3,3,2,1])

    # PASTILLE
    if bot["mode"] == "OFF":
        col0.write("⚫")
    elif bot["mode"] == "BUY":
        col0.write("🟢")
    else:
        col0.write("🔴")

    bot["usdc"] = colU.number_input("USDC", min_value=5.0, value=float(bot["usdc"]), key=f"usdc{i}")

    bot["buy_trigger"] = col1.number_input(
        "Buy si ≤", value=float(bot["buy_trigger"]), format="%.4f", key=f"buy{i}"
    )

    bot["sell_price"] = col2.number_input(
        "Sell LIMIT ≥", value=float(bot["sell_price"]), format="%.4f", key=f"sell{i}"
    )

    col3.metric("Gain", f"{bot['gain']:.4f}")
    col4.metric("Cycles", bot["cycles"])

    # START / STOP
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

    # DELETE
    if col6.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()


# ----------------------------------------------------
# LOGIQUE TRADING
# ----------------------------------------------------
now = time.time()
if now - st.session_state.last_run > 2:

    st.session_state.last_run = now
    prix = get_price()
    if prix is None:
        st.stop()

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        # ---------------- BUY MARKET ----------------
        if bot["mode"] == "BUY" and prix <= bot["buy_trigger"]:

            qty = round(bot["usdc"] / prix, 6)
            if qty < 5:
                continue

            try:
                order = exchange.create_market_buy_order("XRP/USDC", qty)
            except Exception as e:
                st.error(f"Erreur Achat MARKET : {e}")
                continue

            filled = order.get("filled", 0)
            if filled < 5:
                continue

            bot["xrp_qty"] = filled
            bot["entry"] = prix
            bot["mode"] = "SELL"
            save_bots()

        # ---------------- SELL LIMIT ----------------
        if bot["mode"] == "SELL":

            sell_qty = round(bot["xrp_qty"], 6)
            if sell_qty < 5:
                continue

            try:
                order = exchange.create_limit_sell_order("XRP/USDC", sell_qty, bot["sell_price"])
                oid = order["id"]
            except Exception as e:
                st.error(f"Erreur Sell LIMIT : {e}")
                continue

            try:
                o = exchange.fetch_order(oid, "XRP/USDC")

                if o["status"] == "closed":

                    gain = (bot["sell_price"] - bot["entry"]) * sell_qty
                    bot["gain"] += gain
                    bot["cycles"] += 1

                    bot["mode"] = "BUY"
                    bot["entry"] = None
                    bot["xrp_qty"] = 0.0

                    save_bots()

            except:
                pass

save_bots()
