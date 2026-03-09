import streamlit as st
import ccxt
import json, os, time
import pandas as pd

st.set_page_config(page_title="Snowball XRP/USDC", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

# ----------------------------------------------------
# LOAD / SAVE
# ----------------------------------------------------
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

# ----------------------------------------------------
# KRACKEN CONNECTION
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
# PRICE
# ----------------------------------------------------
def get_price():
    try:
        return exchange.fetch_ticker("XRP/USDC")["last"]
    except:
        return None

prix = get_price()
if prix is None:
    st.error("Impossible d'obtenir le prix actuel.")
    st.stop()

st.title("❄️ Bot Snowball XRP/USDC")
st.metric("Prix XRP/USDC", f"{prix:.5f}")

# ----------------------------------------------------
# BALANCES
# ----------------------------------------------------
bal = exchange.fetch_balance()
usdc = bal["free"].get("USDC", 0.0)
xrp  = bal["free"].get("XRP", 0.0)

st.metric("USDC Disponible", f"{usdc:.3f}")
st.metric("XRP Disponible", f"{xrp:.3f}")

# ----------------------------------------------------
# MIGRATION SÉCURITÉ
# ----------------------------------------------------
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

save_bots()

# ----------------------------------------------------
# RESET BOTS
# ----------------------------------------------------
if "reset_lock" not in st.session_state:
    st.session_state.reset_lock = False

if st.button("🧹 Reset Bots") and not st.session_state.reset_lock:
    st.session_state.reset_lock = True
    st.session_state.bots = []
    with open(SAVE_FILE, "w") as f:
        f.write("[]")
    st.success("Bots réinitialisés.")
    time.sleep(0.3)
    st.session_state.reset_lock = False
    st.rerun()

# ----------------------------------------------------
# ADD BOT
# ----------------------------------------------------
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
        "cycles": 0
    })
    save_bots()
    st.rerun()

# ----------------------------------------------------
# DISPLAY BOTS — HORIZONTAL
# ----------------------------------------------------
st.subheader("🤖 Vos Bots")

for i, bot in enumerate(st.session_state.bots):

    st.markdown("---")

    col0, col1, col2, col3, col4, col5, col6 = st.columns([1,3,3,3,2,2,1])

    # STATUS ICON
    if bot["mode"] == "CONFIG":
        col0.write("⚙️")
    elif bot["mode"] == "BUY":
        col0.write("🟢")
    elif bot["mode"] == "SELL":
        col0.write("🔴")
    else:
        col0.write("🟡")

    # INPUTS
    bot["target_usdc"] = col1.number_input("", value=float(bot["target_usdc"]), key=f"u{i}", label_visibility="collapsed")
    col1.caption("Montant USDC")

    bot["buy_price"] = col2.number_input("", value=float(bot["buy_price"]), format="%.5f", key=f"b{i}", label_visibility="collapsed")
    col2.caption("Prix Achat")

    bot["sell_price"] = col3.number_input("", value=float(bot["sell_price"]), format="%.5f", key=f"s{i}", label_visibility="collapsed")
    col3.caption("Prix Vente")

    bot["snowball"] = col4.checkbox("Snowball", value=bot["snowball"], key=f"sn{i}")

    # START
    if not bot["enabled"]:
        if col5.button("Start", key=f"start{i}"):
            bot["enabled"] = True
            try:
                qty = round(bot["target_usdc"] / bot["buy_price"], 6)
                exchange.create_limit_buy_order("XRP/USDC", qty, bot["buy_price"])
                bot["xrp_qty"] = qty
                bot["mode"] = "BUY"
            except:
                bot["enabled"] = False
                bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()
    else:
        if col5.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()

    # DELETE
    if col6.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()

    # ----------------------------------------------------
    # INFO LINE : Gain | Cycles | Achat | Vente | Spread | Prix marché
    # ----------------------------------------------------
    spread = (bot["sell_price"] - bot["buy_price"]) / bot["buy_price"] * 100 if bot["buy_price"] else 0

    colI1, colI2, colI3, colI4, colI5, colI6 = st.columns(6)

    colI1.metric("Gain", f"{bot['gain']:.4f}")
    colI2.metric("Cycles", bot["cycles"])
    colI3.metric("Achat", f"{bot['buy_price']:.5f}")
    colI4.metric("Vente", f"{bot['sell_price']:.5f}")
    colI5.metric("Spread %", f"{spread:.3f}")
    colI6.metric("Marché", f"{prix:.5f}")

# ----------------------------------------------------
# TRADING LOOP
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
            try:
                exchange.create_limit_sell_order("XRP/USDC", qty, bot["sell_price"])
            except:
                continue

            bot["gain"] += (bot["sell_price"] - bot["buy_price"]) * qty
            bot["cycles"] += 1

            if bot["snowball"]:
                qty2 = round(bot["target_usdc"] / bot["buy_price"], 6)
                exchange.create_limit_buy_order("XRP/USDC", qty2, bot["buy_price"])
                bot["xrp_qty"] = qty2
                bot["mode"] = "BUY"
            else:
                bot["enabled"] = False
                bot["mode"] = "CONFIG"

            save_bots()

# ----------------------------------------------------
# KRAKEN ORDERS VIEW
# ----------------------------------------------------
st.header("📑 Ordres Kraken")

try:
    open_orders = exchange.fetch_open_orders("XRP/USDC")
    closed_orders = exchange.fetch_closed_orders("XRP/USDC")
except:
    st.error("Impossible d'obtenir les ordres.")
    open_orders, closed_orders = [], []

st.subheader("🟡 Ordres en attente")
if not open_orders:
    st.info("Aucun ordre en attente.")
else:
    df_open = pd.DataFrame([{
        "ID": o["id"],
        "Type": o["side"],
        "Prix": o["price"],
        "Quantité": o["amount"],
        "Statut": o["status"]
    } for o in open_orders])
    st.dataframe(df_open, use_container_width=True)

st.subheader("🟢 Ordres exécutés")
if not closed_orders:
    st.info("Aucun ordre exécuté.")
else:
    df_closed = pd.DataFrame([{
        "ID": o["id"],
        "Type": o["side"],
        "Prix": o["price"],
        "Quantité": o["amount"],
        "Statut": o["status"]
    } for o in closed_orders[-20:]])
    st.dataframe(df_closed, use_container_width=True)

save_bots()
