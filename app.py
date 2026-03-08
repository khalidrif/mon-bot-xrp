import streamlit as st
import ccxt
import json, os, time

st.set_page_config(page_title="Bots Snowball XRP/USDC", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

# ----------------------------------------------------
# STYLE COMPACT iPHONE
# ----------------------------------------------------
st.markdown("""
<style>
body { zoom: 95%; }
.bot {
    border: 1px solid #cccccc55;
    border-radius: 10px;
    padding: 6px;
    margin-bottom: 8px;
    background: #f8f8f8;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# SAVE / LOAD
# ----------------------------------------------------
def load_bots():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            bots = json.load(f)
    else:
        return []

    # auto-fix
    for bot in bots:
        bot.setdefault("enabled", False)
        bot.setdefault("mode", "OFF")
        bot.setdefault("usdc", 10.0)
        bot.setdefault("buy_trigger", 0.0)
        bot.setdefault("sell_price", 0.0)
        bot.setdefault("entry", None)
        bot.setdefault("xrp_qty", 0.0)
        bot.setdefault("gain", 0.0)
        bot.setdefault("cycles", 0)
    return bots

def save_bots():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)

# ----------------------------------------------------
# INIT
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
# PRICE
# ----------------------------------------------------
def get_price():
    try:
        return exchange.fetch_ticker("XRP/USDC")["last"]
    except:
        return None

prix = get_price()
if prix is None:
    st.error("Erreur récupération prix.")
    st.stop()

st.title("❄️ Snowball XRP/USDC – Version Anti-Erreurs Kraken")
st.metric("Prix XRP/USDC", f"{prix:.5f}")

# ----------------------------------------------------
# BALANCE USDC
# ----------------------------------------------------
try:
    bal = exchange.fetch_balance()
    usdc_kraken = bal["free"].get("USDC", 0.0)
except:
    usdc_kraken = 0.0

st.metric("USDC Kraken", f"{usdc_kraken:.5f}")

# ----------------------------------------------------
# ADD BOT
# ----------------------------------------------------
if st.button("➕ Ajouter Bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "OFF",
        "usdc": 10.0,  # minimum obligatoire
        "buy_trigger": round(prix * 0.99, 5),
        "sell_price": round(prix * 1.01, 5),
        "entry": None,
        "xrp_qty": 0.0,
        "gain": 0.0,
        "cycles": 0
    })
    save_bots()
    st.rerun()

# ----------------------------------------------------
# DISPLAY BOTS
# ----------------------------------------------------
for i, bot in enumerate(st.session_state.bots):

    st.markdown("<div class='bot'>", unsafe_allow_html=True)

    col0, colUSDC, col1, col2 = st.columns([1,3,4,2])

    col0.write("⚫" if bot["mode"]=="OFF" else ("🟢" if bot["mode"]=="BUY" else "🔴"))
    colUSDC.write(f"USDC Bot : **{bot['usdc']}**")

    bot["buy_trigger"] = col1.number_input(
        "Buy ≤",
        value=float(bot["buy_trigger"]),
        format="%.5f",
        key=f"buy{i}"
    )

    bot["sell_price"] = col2.number_input(
        "Sell LIMIT ≥",
        value=float(bot["sell_price"]),
        format="%.5f",
        key=f"sell{i}"
    )

    colA, colB, colC, colD, colDel = st.columns([2,2,2,2,1])
    colA.metric("Gain", f"{bot['gain']:.4f}")
    colB.metric("Cycles", bot["cycles"])

    # START / STOP
    if bot["enabled"]:
        if colC.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "OFF"
            bot["entry"] = None
            save_bots()
            st.rerun()
    else:
        if colC.button("Start", key=f"start{i}"):
            bot["enabled"] = True
            bot["mode"] = "BUY"
            save_bots()
            st.rerun()

    # DELETE BOT
    if colDel.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# TRADING LOOP (2 SECONDS)
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

        # ------------------- BUY MARKET (NEVER PARTIAL) -------------------
        if bot["mode"] == "BUY" and prix <= bot["buy_trigger"]:

            qty = round(bot["usdc"] / prix, 6)
            if qty < 5:
                continue  # kraken min

            try:
                order = exchange.create_market_buy_order("XRP/USDC", qty)
            except Exception as e:
                st.error(f"Achat MARKET erreur: {e}")
                continue

            filled = order.get("filled", 0)
            if filled < 5:
                continue

            bot["xrp_qty"] = filled
            bot["entry"] = prix
            bot["mode"] = "SELL"
            save_bots()

        # ------------------- SELL LIMIT (MUST COST ≥ 5 USDC) -------------------
        elif bot["mode"] == "SELL":

            sell_qty = round(bot["xrp_qty"], 6)
            if sell_qty < 5:
                continue

            sell_price = round(float(bot["sell_price"]), 5)

            # FIX : coût minimum 5 USDC
            cost = sell_qty * sell_price
            if cost < 5:
                continue  # attendre meilleur prix

            try:
                order = exchange.create_limit_sell_order("XRP/USDC", sell_qty, sell_price)
                oid = order["id"]
            except Exception as e:
                st.error(f"Erreur Sell LIMIT : {e} | prix {sell_price}")
                continue

            try:
                o = exchange.fetch_order(oid, "XRP/USDC")
                if o["status"] == "closed":

                    gain = (sell_price - bot["entry"]) * sell_qty
                    bot["gain"] += gain
                    bot["cycles"] += 1

                    # reset cycle
                    bot["entry"] = None
                    bot["xrp_qty"] = 0.0
                    bot["mode"] = "BUY"
                    save_bots()

            except:
                pass

save_bots()
