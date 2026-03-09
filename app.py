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
# MIGRATION (sécurité)
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
    bot.setdefault("last_usdc_value", 0.0)

save_bots()

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
# PRICE
# ----------------------------------------------------
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


# ----------------------------------------------------
# BALANCES
# ----------------------------------------------------
bal = exchange.fetch_balance()
usdc = bal["free"].get("USDC", 0.0)
xrp  = bal["free"].get("XRP", 0.0)

st.metric("USDC Disponible", f"{usdc:.3f}")
st.metric("XRP Disponible", f"{xrp:.3f}")


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
        "cycles": 0,
        "last_usdc_value": 0.0
    })
    save_bots()
    st.rerun()


# ----------------------------------------------------
# DISPLAY BOTS — HORIZONTAL
# ----------------------------------------------------
st.subheader("🤖 Vos Bots")

for i, bot in enumerate(st.session_state.bots):

    st.markdown("---")

    colStatus, colUSDC, colBuy, colSell, colSnow, colGain, colCycles, colQty, colStart, colDelete = st.columns([1,3,3,3,2,2,2,2,2,1])

    # Status icon
    if bot["mode"] == "CONFIG":
        colStatus.write("⚙️")
    elif bot["mode"] == "BUY":
        colStatus.write("🟢")
    elif bot["mode"] == "SELL":
        colStatus.write("🔴")
    else:
        colStatus.write("🟡")

    # INPUTS
    bot["target_usdc"] = colUSDC.number_input("", value=float(bot["target_usdc"]), key=f"u{i}", label_visibility="collapsed")
    bot["buy_price"]   = colBuy.number_input("", value=float(bot["buy_price"]), format="%.5f", key=f"b{i}", label_visibility="collapsed")
    bot["sell_price"]  = colSell.number_input("", value=float(bot["sell_price"]), format="%.5f", key=f"s{i}", label_visibility="collapsed")

    colUSDC.caption("Montant")
    colBuy.caption("Achat")
    colSell.caption("Vente")

    bot["snowball"] = colSnow.checkbox("Snowball", value=bot["snowball"], key=f"sn{i}")

    # Gain + Cycles (petits)
    colGain.markdown(f"<div style='font-size:14px;'><b>Gain</b><br>{bot['gain']:.4f}</div>", unsafe_allow_html=True)
    colCycles.markdown(f"<div style='font-size:14px;'><b>Cycles</b><br>{bot['cycles']}</div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # USDC VALUE dynamic colored
    # ----------------------------------------------------
    usdc_value = bot["xrp_qty"] * prix

    if usdc_value > bot["last_usdc_value"]:
        usdc_color = "green"
    elif usdc_value < bot["last_usdc_value"]:
        usdc_color = "red"
    else:
        usdc_color = "white"

    colQty.markdown(
        f"<div style='font-size:14px;color:{usdc_color};'><b>USDC</b><br>{usdc_value:.4f}</div>",
        unsafe_allow_html=True
    )

    bot["last_usdc_value"] = usdc_value

    # START / STOP
    if not bot["enabled"]:
        if colStart.button("Start", key=f"start{i}"):
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
        if colStart.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()

    # DELETE BOT
    if colDelete.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()


# ----------------------------------------------------
# TRADING LOOP
# ----------------------------------------------------
now = time.time()
if now - st.session_state.last_run > 2:

    st.session_state.last_run = now
    prix = get_price()

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
# ORDERS (TABLEAU)
# ----------------------------------------------------
st.header("📑 Ordres Kraken")

try:
    open_orders = exchange.fetch_open_orders("XRP/USDC")
    closed_orders = exchange.fetch_closed_orders("XRP/USDC")
except:
    st.error("Erreur ordres.")
    open_orders, closed_orders = [], []


# ----------------------------------------------------
# VUE SIMPLE COLOREE (BUY=VERT, SELL=ROUGE)
# ----------------------------------------------------
st.subheader("📌 Vue simple des ordres ouverts")

if not open_orders:
    st.info("Aucun ordre en attente.")
else:
    for o in open_orders:
        couleur = "green" if o["side"] == "buy" else "red"
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(o["timestamp"]/1000))

        st.markdown(
            f"<div style='font-size:15px;color:{couleur};'>"
            f"<b>{o['id']}</b> — {o['side']} — {o['price']} — {o['amount']} XRP — {date_str}"
            f"</div>",
            unsafe_allow_html=True
        )


st.subheader("📌 Historique simple")

if not closed_orders:
    st.info("Aucun ordre exécuté.")
else:
    for o in closed_orders[-20:]:
        couleur = "green" if o["side"] == "buy" else "red"
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(o["timestamp"]/1000))

        st.markdown(
            f"<div style='font-size:15px;color:{couleur};'>"
            f"<b>{o['id']}</b> — {o['side']} — {o['price']} — {o['amount']} XRP — {date_str}"
            f"</div>",
            unsafe_allow_html=True
        )


# ----------------------------------------------------
# ORDERS (TABLEAU)
# ----------------------------------------------------
st.subheader("🟡 Ordres en attente (tableau)")
if open_orders:
    df_open = pd.DataFrame(open_orders)
    st.dataframe(df_open, use_container_width=True)
else:
    st.info("Aucun ordre en attente.")

st.subheader("🟢 Ordres exécutés (tableau)")
if closed_orders:
    df_closed = pd.DataFrame(closed_orders[-20:])
    st.dataframe(df_closed, use_container_width=True)
else:
    st.info("Aucun ordre exécuté.")

save_bots()
