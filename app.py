import streamlit as st
import ccxt
import json, os, time

st.set_page_config(page_title="Snowball XRP/USDC", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

# ----------------------------------------------------
# STYLE
# ----------------------------------------------------
st.markdown("""
<style>
body { zoom: 92%; }
.bot {
    border: 1px solid #cccccc55;
    border-radius: 8px;
    padding: 8px;
    margin-bottom: 10px;
    background: #fafafa;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# LOAD / SAVE
# ----------------------------------------------------
def load_bots():
    if not os.path.exists(SAVE_FILE):
        return []
    with open(SAVE_FILE, "r") as f:
        return json.load(f)

def save_bots():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)

if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

# ----------------------------------------------------
# MIGRATION — évite KeyError
# ----------------------------------------------------
for bot in st.session_state.bots:
    bot.setdefault("enabled", True)
    bot.setdefault("mode", "CONFIG")  # <-- IMPORTANT
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
    st.error("Impossible d'obtenir le prix.")
    st.stop()

st.title("❄️ Bot Snowball XRP/USDC")
st.metric("Prix XRP/USDC", f"{prix:.5f}")

# ----------------------------------------------------
# BALANCES
# ----------------------------------------------------
bal = exchange.fetch_balance()
usdc = bal["free"].get("USDC", 0.0)
xrp = bal["free"].get("XRP", 0.0)

colBal1, colBal2 = st.columns(2)
colBal1.metric("USDC Disponible", f"{usdc:.3f}")
colBal2.metric("XRP Disponible", f"{xrp:.3f}")

# ----------------------------------------------------
# AJOUT BOT — NE FAIT RIEN AUTOMATIQUEMENT !!
# ----------------------------------------------------
if st.button("➕ Ajouter Bot"):
    st.session_state.bots.append({
        "enabled": True,
        "mode": "CONFIG",      # <-- MODE PAR DÉFAUT, PAS D'ACTION AUTOMATIQUE
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

# ----------------------------------------------------
# DISPLAY BOTS
# ----------------------------------------------------
for i, bot in enumerate(st.session_state.bots):

    st.markdown("<div class='bot'>", unsafe_allow_html=True)

    col0, col1, col2, col3, col4 = st.columns([1,3,3,3,2])

    # STATUS
    if bot["mode"] == "CONFIG":
        col0.write("⚙️")
    elif bot["mode"] == "WAIT_BUY":
        col0.write("🟡")
    elif bot["mode"] == "BUY":
        col0.write("🟢")
    else:
        col0.write("🔴")

    # INPUTS
    bot["target_usdc"] = col1.number_input("Montant (USDC)", value=float(bot["target_usdc"]), min_value=0.0, key=f"u{i}")
    bot["buy_price"]   = col2.number_input("Prix Achat", value=float(bot["buy_price"]), min_value=0.0, format="%.5f", key=f"b{i}")
    bot["sell_price"]  = col3.number_input("Prix Vente", value=float(bot["sell_price"]), min_value=0.0, format="%.5f", key=f"s{i}")
    bot["snowball"]    = col4.checkbox("Snowball ♻️", value=bot["snowball"], key=f"sn{i}")

    colA, colB, colC, colDel = st.columns([2,2,2,1])
    colA.metric("Gain total", f"{bot['gain']:.4f}")
    colB.metric("Cycles", bot["cycles"])

    if bot["enabled"]:
        if colC.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()
    else:
        if colC.button("Start", key=f"start{i}"):
            bot["enabled"] = True
            bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()

    if colDel.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# TRADING LOOP
# ----------------------------------------------------
now = time.time()
if now - st.session_state.last_run > 2:

    st.session_state.last_run = now
    prix = get_price()
    if prix is None:
        st.stop()

    bal = exchange.fetch_balance()
    usdc = bal["free"].get("USDC", 0.0)
    xrp = bal["free"].get("XRP", 0.0)

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        # ----------------------------------------------------
        # MODE CONFIG → attendre que l’utilisateur remplisse tout
        # ----------------------------------------------------
        if bot["mode"] == "CONFIG":

            if bot["target_usdc"] > 0 and bot["buy_price"] > 0 and bot["sell_price"] > 0:
                bot["mode"] = "WAIT_BUY"
                save_bots()

            continue

        # ----------------------------------------------------
        # WAIT_BUY → acheter seulement si prix <= buy_price
        # ----------------------------------------------------
        if bot["mode"] == "WAIT_BUY":

            if prix <= bot["buy_price"] and usdc >= bot["target_usdc"]:

                qty = round(bot["target_usdc"] / prix, 6)
                if qty < 5:
                    continue

                try:
                    order = exchange.create_limit_buy_order("XRP/USDC", qty, bot["buy_price"])
                    bot["xrp_qty"] = qty
                    bot["mode"] = "SELL"
                except:
                    continue

            save_bots()
            continue

        # ----------------------------------------------------
        # SELL → vendre seulement si prix >= sell_price
        # ----------------------------------------------------
        if bot["mode"] == "SELL":

            if prix < bot["sell_price"]:
                continue  # <-- IMPORTANT : PAS DE VENTE !

            qty = round(xrp, 6)
            if qty < 5:
                continue

            try:
                order = exchange.create_limit_sell_order("XRP/USDC", qty, bot["sell_price"])
                oid = order["id"]
            except:
                continue

            o = exchange.fetch_order(oid, "XRP/USDC")
            if o["status"] == "closed":

                gain = (bot["sell_price"] - bot["buy_price"]) * qty
                bot["gain"] += gain
                bot["cycles"] += 1

                if bot["snowball"]:
                    bot["mode"] = "WAIT_BUY"
                else:
                    bot["enabled"] = False

                save_bots()

save_bots()
