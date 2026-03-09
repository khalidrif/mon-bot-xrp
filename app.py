import streamlit as st
import ccxt
import json, os, time
import pandas as pd

st.set_page_config(page_title="Snowball XRP", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

# ---------------------------
# LOAD / SAVE
# ---------------------------
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

# ---------------------------
# MIGRATION
# ---------------------------
for bot in st.session_state.bots:
    bot.setdefault("enabled", False)
    bot.setdefault("mode", "CONFIG")
    bot.setdefault("target_usdc", 0.0)
    bot.setdefault("buy_price", 0.0)
    bot.setdefault("sell_price", 0.0)
    bot.setdefault("xrp_qty", 0.0)
    bot.setdefault("snowball", True)
    bot.setdefault("gain", 0.0)
    bot.setdefault("cycles", 0)
    bot.setdefault("last_usdc_value", 0.0)
    bot.setdefault("pair", "XRP/USDC")

save_bots()

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
# PRICE
# ---------------------------
def get_price():
    for p in ["XRP/USDC", "XRP/USDT", "XRP/USD"]:
        try:
            return exchange.fetch_ticker(p)["last"]
        except:
            pass
    return None

prix = get_price()
if prix is None:
    st.error("Erreur prix")
    st.stop()

st.title("❄️ Bot Snowball XRP")
st.metric("Prix", f"{prix:.5f}")

# ---------------------------
# BALANCES
# ---------------------------
bal = exchange.fetch_balance()
usd = bal["free"].get("USDC", 0) + bal["free"].get("USDT", 0) + bal["free"].get("USD", 0)
xrp = bal["free"].get("XRP", 0)

st.metric("USD Disponible", f"{usd:.4f}")
st.metric("XRP Disponible", f"{xrp:.4f}")

# ---------------------------
# RESET
# ---------------------------
if "reset_lock" not in st.session_state:
    st.session_state.reset_lock = False

if st.button("🧹 Reset Bots") and not st.session_state.reset_lock:
    st.session_state.reset_lock = True
    st.session_state.bots = []
    with open(SAVE_FILE, "w") as f:
        f.write("[]")
    time.sleep(0.2)
    st.session_state.reset_lock = False
    st.rerun()

# ---------------------------
# ADD BOT
# ---------------------------
if st.button("➕ Ajouter Bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "CONFIG",
        "target_usdc": 0.0,
        "buy_price": 0.0,
        "sell_price": 0.0,
        "xrp_qty": 0.0,
        "snowball": True,
        "gain": 0.0,
        "cycles": 0,
        "last_usdc_value": 0.0,
        "pair": "XRP/USDC"
    })
    save_bots()
    st.rerun()

# ---------------------------
# DISPLAY BOTS
# ---------------------------
st.subheader("🤖 Vos Bots")

for i, bot in enumerate(st.session_state.bots):

    st.write("----------------------------------------------------")
    colS, colU, colB, colV, colSN, colG, colC, colUSDC, colStart, colDel = st.columns([1,3,3,3,2,2,2,2,2,1])

    # ICON
    if bot["mode"] == "CONFIG": colS.write("⚙️")
    elif bot["mode"] == "BUY": colS.write("🟢")
    elif bot["mode"] == "SELL": colS.write("🔴")
    else: colS.write("🟡")

    # INPUTS
    bot["target_usdc"] = colU.number_input("", value=float(bot["target_usdc"]), key=f"u{i}", label_visibility="collapsed")
    colU.caption("Montant")

    bot["buy_price"] = colB.number_input("", value=float(bot["buy_price"]), format="%.5f", key=f"b{i}", label_visibility="collapsed")
    colB.caption("Achat")

    bot["sell_price"] = colV.number_input("", value=float(bot["sell_price"]), format="%.5f", key=f"s{i}", label_visibility="collapsed")
    colV.caption("Vente")

    bot["snowball"] = colSN.checkbox("Snowball", value=bot["snowball"], key=f"sn{i}")

    # Gain + Cycles
    colG.markdown(f"<div style='font-size:14px;'><b>Gain</b><br>{bot['gain']:.4f}</div>", unsafe_allow_html=True)
    colC.markdown(f"<div style='font-size:14px;'><b>Cycles</b><br>{bot['cycles']}</div>", unsafe_allow_html=True)

    # USDC VALUE
    usdc_val = bot["xrp_qty"] * prix

    if usdc_val > bot["last_usdc_value"]:
        color = "green"
    elif usdc_val < bot["last_usdc_value"]:
        color = "red"
    else:
        color = "white"

    colUSDC.markdown(f"<div style='font-size:14px;color:{color};'><b>USDC</b><br>{usdc_val:.4f}</div>", unsafe_allow_html=True)
    bot["last_usdc_value"] = usdc_val

    # START / STOP
    if not bot["enabled"]:

        if colStart.button("Start", key=f"st{i}"):

            bot["enabled"] = True

            try:
                qty = round(bot["target_usdc"] / bot["buy_price"], 6)
                order = exchange.create_limit_buy_order("XRP/USDC", qty, bot["buy_price"])

                bot["pair"] = order["symbol"]
                bot["xrp_qty"] = qty
                bot["mode"] = "BUY"

            except:
                bot["enabled"] = False
                bot["mode"] = "CONFIG"

            save_bots()
            st.rerun()

    else:
        if colStart.button("Stop", key=f"sp{i}"):
            bot["enabled"] = False
            bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()

    if colDel.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()

# ---------------------------
# TRADING LOOP
# ---------------------------
now = time.time()
if now - st.session_state.last_run > 2:

    st.session_state.last_run = now
    prix = get_price()

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        # WAIT BUY EXECUTION
        if bot["mode"] == "BUY":

            try:
                op = exchange.fetch_open_orders(bot["pair"])
            except:
                op = []

            # BUY is filled → SEND SELL IMMEDIATELY
            if len(op) == 0:

                qty = round(bot["xrp_qty"], 6)

                try:
                    order = exchange.create_limit_sell_order(bot["pair"], qty, bot["sell_price"])
                    bot["pair"] = order["symbol"]
                except:
                    continue

                bot["mode"] = "SELL"
                save_bots()

            continue

        # SELL MODE (order already created)
        if bot["mode"] == "SELL":

            # if order still open → wait
            continue

# ---------------------------
# FETCH ALL ORDERS
# ---------------------------
open_orders = []
closed_orders = []

for p in ["XRP/USDC", "XRP/USDT", "XRP/USD"]:
    try: open_orders += exchange.fetch_open_orders(p)
    except: pass
    try: closed_orders += exchange.fetch_closed_orders(p)
    except: pass

# ---------------------------
# DISPLAY ORDERS
# ---------------------------
st.header("📑 Ordres Kraken")

st.subheader("Ordres ouverts")
if not open_orders:
    st.info("Aucun ordre ouvert.")
else:
    for o in open_orders:
        c = "green" if o["side"] == "buy" else "red"
        d = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(o["timestamp"]/1000))
        st.markdown(f"<div style='color:{c};'>{o['id']} — {o['side']} — {o['price']} — {o['amount']} XRP — {d}</div>", unsafe_allow_html=True)

st.subheader("Ordres exécutés")
if not closed_orders:
    st.info("Aucun ordre exécuté.")
else:
    for o in closed_orders[-20:]:
        c = "green" if o["side"] == "buy" else "red"
        d = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(o["timestamp"]/1000))
        st.markdown(f"<div style='color:{c};'>{o['id']} — {o['side']} — {o['price']} — {o['amount']} XRP — {d}</div>", unsafe_allow_html=True)

save_bots()
