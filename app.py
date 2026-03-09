import streamlit as st
import ccxt
import json, os, time, threading

st.set_page_config(page_title="Snowball XRP", page_icon="❄️", layout="wide")
SAVE_FILE = "bots.json"
LOCK = threading.Lock()

def load_bots():
    if not os.path.exists(SAVE_FILE):
        return []
    try:
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_bots():
    with LOCK:
        with open(SAVE_FILE, "w") as f:
            json.dump(st.session_state.bots, f, indent=4)

if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

# defaults / migration
for bot in st.session_state.bots:
    bot.setdefault("enabled", False)
    bot.setdefault("mode", "CONFIG")
    bot.setdefault("target_usdc", 10.0)
    bot.setdefault("buy_price", 0.0)
    bot.setdefault("sell_price", 0.0)
    bot.setdefault("xrp_qty", 0.0)
    bot.setdefault("snowball", True)
    bot.setdefault("gain", 0.0)
    bot.setdefault("cycles", 0)
    bot.setdefault("pair", "XRP/USDC")
    bot.setdefault("buy_id", "")
    bot.setdefault("sell_id", "")

save_bots()

exchange = ccxt.kraken({
    "apiKey": st.secrets["KRAKEN_KEY"],
    "secret": st.secrets["KRAKEN_SECRET"],
    "enableRateLimit": True
})

def get_price():
    for p in ["XRP/USDC", "XRP/USDT", "XRP/USD"]:
        try:
            return exchange.fetch_ticker(p)["last"]
        except Exception:
            pass
    return 0.0

prix = get_price()

st.title("❄️ Snowball XRP Bot")
st.metric("Prix XRP", f"{prix:.5f}")

# BALANCE
try:
    bal = exchange.fetch_balance()
except Exception as e:
    st.error(f"Erreur fetch_balance: {e}")
    bal = {"free": {}}
usd = bal["free"].get("USDC", 0) + bal["free"].get("USDT", 0) + bal["free"].get("USD", 0)
xrp = bal["free"].get("XRP", 0)
st.metric("USD", f"{usd:.2f}")
st.metric("XRP", f"{xrp:.2f}")

# ADD BOT
if st.button("➕ Ajouter Bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "CONFIG",
        "target_usdc": 10,
        "buy_price": 0,
        "sell_price": 0,
        "xrp_qty": 0,
        "snowball": True,
        "gain": 0,
        "cycles": 0,
        "pair": "XRP/USDC",
        "buy_id": "",
        "sell_id": ""
    })
    save_bots()
    st.experimental_rerun()  # rerun only after adding

st.subheader("Bots")
for i, bot in enumerate(st.session_state.bots):
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    bot["target_usdc"] = col1.number_input("USDC", value=float(bot["target_usdc"]), key=f"u{i}")
    bot["buy_price"] = col2.number_input("BUY", value=float(bot["buy_price"]), format="%.5f", key=f"b{i}")
    bot["sell_price"] = col3.number_input("SELL", value=float(bot["sell_price"]), format="%.5f", key=f"s{i}")
    bot["snowball"] = col4.checkbox("Snowball", value=bot["snowball"], key=f"sn{i}")
    col5.write(f"Gain {bot['gain']:.4f}")
    col6.write(f"Cycles {bot['cycles']}")

    if not bot["enabled"]:
        if col7.button("Start", key=f"start{i}"):
            if bot["buy_price"] <= 0 or bot["sell_price"] <= 0 or bot["target_usdc"] <= 0:
                st.error("Vérifie buy_price, sell_price et target_usdc (>0).")
            else:
                try:
                    # load markets if needed
                    if not exchange.markets:
                        exchange.load_markets()
                    qty = bot["target_usdc"] / bot["buy_price"]
                    try:
                        qty = float(exchange.amount_to_precision(bot["pair"], qty))
                    except Exception:
                        qty = round(qty, 4)
                    order = exchange.create_limit_buy_order(bot["pair"], qty, bot["buy_price"])
                    bot["buy_id"] = order.get("id", "")
                    bot["xrp_qty"] = qty
                    bot["mode"] = "BUY"
                    bot["enabled"] = True
                    save_bots()
                except Exception as e:
                    st.error(f"Erreur création BUY: {e}")
                st.experimental_rerun()  # rerun after start
    else:
        if col7.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "CONFIG"
            save_bots()
            st.experimental_rerun()  # rerun after stop

# TRADING LOOP in background thread
def trading_loop():
    while True:
        for bot in st.session_state.bots:
            if not bot.get("enabled"):
                continue
            pair = bot.get("pair")
            # BUY waiting
            if bot.get("mode") == "BUY" and bot.get("buy_id"):
                try:
                    order = exchange.fetch_order(bot["buy_id"], pair)
                except Exception:
                    continue
                filled = float(order.get("filled", 0))
                amount = float(order.get("amount", 0) or 0)
                status = (order.get("status") or "").lower()
                is_filled = (status == "closed") or (amount > 0 and abs(filled - amount) < 1e-8) or (order.get("remaining", 1) == 0)
                if is_filled:
                    try:
                        sell_qty = bot["xrp_qty"]
                        try:
                            sell_qty = float(exchange.amount_to_precision(pair, sell_qty))
                        except Exception:
                            sell_qty = round(sell_qty, 4)
                        sell = exchange.create_limit_sell_order(pair, sell_qty, bot["sell_price"])
                        bot["sell_id"] = sell.get("id", "")
                        bot["mode"] = "SELL"
                        bot["buy_id"] = ""
                        save_bots()
                    except Exception:
                        pass
            # SELL waiting
            elif bot.get("mode") == "SELL" and bot.get("sell_id"):
                try:
                    order = exchange.fetch_order(bot["sell_id"], pair)
                except Exception:
                    continue
                filled = float(order.get("filled", 0))
                amount = float(order.get("amount", 0) or 0)
                status = (order.get("status") or "").lower()
                is_filled = (status == "closed") or (amount > 0 and abs(filled - amount) < 1e-8) or (order.get("remaining", 1) == 0)
                if is_filled:
                    gain = (bot["sell_price"] - bot["buy_price"]) * bot["xrp_qty"]
                    bot["gain"] = bot.get("gain", 0) + gain
                    bot["cycles"] = bot.get("cycles", 0) + 1
                    if bot.get("snowball"):
                        bot["target_usdc"] = round(float(bot.get("target_usdc", 0)) + gain, 8)
                        if bot["target_usdc"] < 0:
                            bot["target_usdc"] = 0
                    bot["mode"] = "CONFIG"
                    bot["xrp_qty"] = 0
                    bot["sell_id"] = ""
                    bot["buy_id"] = ""
                    save_bots()
        time.sleep(2)

if "trading_thread" not in st.session_state:
    t = threading.Thread(target=trading_loop, daemon=True)
    st.session_state.trading_thread = t
    t.start()
