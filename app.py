import streamlit as st
import ccxt
import json, os, time

st.set_page_config(page_title="Snowball XRP/USDC", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

def load_bots():
    if not os.path.exists(SAVE_FILE):
        return []
    try:
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_bots():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)

if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

for bot in st.session_state.bots:
    bot.setdefault("enabled", False)
    bot.setdefault("mode", "CONFIG")
    bot.setdefault("target_usdc", 0.0)
    bot.setdefault("buy_price", 0.0)
    bot.setdefault("sell_price", 0.0)
    bot.setdefault("snowball", True)
    bot.setdefault("gain", 0.0)
    bot.setdefault("cycles", 0)
    bot.setdefault("xrp_qty", 0.0)

save_bots()

if "last_run" not in st.session_state:
    st.session_state.last_run = 0

try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True
    })
except:
    st.error("Erreur API Kraken")
    st.stop()

def get_price():
    try:
        return exchange.fetch_ticker("XRP/USDC")["last"]
    except:
        return None

prix = get_price()
if prix is None:
    st.error("Erreur prix.")
    st.stop()

st.title("❄️ Bot Snowball XRP/USDC")
st.metric("Prix XRP/USDC", f"{prix:.5f}")

bal = exchange.fetch_balance()
usdc = bal["free"].get("USDC", 0.0)
xrp = bal["free"].get("XRP", 0.0)

st.metric("USDC Disponible", f"{usdc:.3f}")
st.metric("XRP Disponible", f"{xrp:.3f}")

if st.button("➕ Ajouter Bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "CONFIG",
        "target_usdc": 0.0,
        "buy_price": 0.0,
        "sell_price": 0.0,
        "snowball": True,
        "gain": 0.0,
        "cycles": 0,
        "xrp_qty": 0.0
    })
    save_bots()
    st.rerun()

if "reset_lock" not in st.session_state:
    st.session_state.reset_lock = False

if st.button("🧹 Reset Bots") and not st.session_state.reset_lock:
    st.session_state.reset_lock = True
    st.session_state.bots = []
    with open(SAVE_FILE, "w") as f:
        f.write("[]")
    st.success("Réinitialisé.")
    time.sleep(0.3)
    st.session_state.reset_lock = False
    st.rerun()

for i, bot in enumerate(st.session_state.bots):

    st.write("——————————————")

    if bot["mode"] == "CONFIG":
        st.write("⚙️ Configuration")
    elif bot["mode"] == "BUY":
        st.write("🟢 Achat en attente/exécution")
    elif bot["mode"] == "SELL":
        st.write("🔴 Vente en attente/exécution")

    bot["target_usdc"] = st.number_input(f"Montant USDC bot {i}", value=float(bot["target_usdc"]), key=f"u{i}")
    bot["buy_price"]   = st.number_input(f"Prix achat bot {i}", value=float(bot["buy_price"]), min_value=0.0, format="%.5f", key=f"b{i}")
    bot["sell_price"]  = st.number_input(f"Prix vente bot {i}", value=float(bot["sell_price"]), min_value=0.0, format="%.5f", key=f"s{i}")
    bot["snowball"]    = st.checkbox(f"Snowball bot {i}", value=bot["snowball"], key=f"sn{i}")

    st.metric(f"Gain bot {i}", f"{bot['gain']:.4f}")
    st.metric(f"Cycles bot {i}", bot["cycles"])

    if not bot["enabled"]:
        if st.button(f"Start bot {i}"):
            bot["enabled"] = True

            try:
                qty = round(bot["target_usdc"] / bot["buy_price"], 6)

                order = exchange.create_limit_buy_order(
                    "XRP/USDC",
                    qty,
                    bot["buy_price"]
                )

                bot["xrp_qty"] = qty
                bot["mode"] = "BUY"

            except:
                bot["enabled"] = False
                bot["mode"] = "CONFIG"

            save_bots()
            st.rerun()

    else:
        if st.button(f"Stop bot {i}"):
            bot["enabled"] = False
            bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()

    if st.button(f"Supprimer bot {i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()

now = time.time()
if now - st.session_state.last_run > 2:

    st.session_state.last_run = now
    prix = get_price()
    if prix is None:
        st.stop()

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        if bot["mode"] == "BUY":

            open_orders = exchange.fetch_open_orders("XRP/USDC")
            if len(open_orders) == 0:
                bot["mode"] = "SELL"
                save_bots()
            continue

        if bot["mode"] == "SELL":

            if prix < bot["sell_price"]:
                continue

            qty = round(bot["xrp_qty"], 6)
            if qty < 5:
                continue

            try:
                order = exchange.create_limit_sell_order("XRP/USDC", qty, bot["sell_price"])
                oid = order["id"]
            except:
                continue

            o = exchange.fetch_order(oid, "XRP/USDC")
            if o["status"] == "closed":

                bot["gain"] += (bot["sell_price"] - bot["buy_price"]) * qty
                bot["cycles"] += 1

                if bot["snowball"]:
                    try:
                        qty2 = round(bot["target_usdc"] / bot["buy_price"], 6)
                        exchange.create_limit_buy_order("XRP/USDC", qty2, bot["buy_price"])
                        bot["xrp_qty"] = qty2
                        bot["mode"] = "BUY"
                    except:
                        bot["enabled"] = False
                        bot["mode"] = "CONFIG"
                else:
                    bot["enabled"] = False
                    bot["mode"] = "CONFIG"

                save_bots()

save_bots()
