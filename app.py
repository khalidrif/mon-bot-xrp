import streamlit as st
import ccxt
import json, os, time

st.set_page_config(page_title="Snowball Auto Montant Cible", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

# ----------------------------------------------------
# STYLE iPHONE COMPACT
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
# PRIX
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

st.title("❄️ Bot Montant-Cible + Snowball XRP/USDC")
st.metric("Prix XRP/USDC", f"{prix:.5f}")

# ----------------------------------------------------
# BALANCES
# ----------------------------------------------------
bal = exchange.fetch_balance()
usdc = bal["free"].get("USDC", 0.0)
xrp = bal["free"].get("XRP", 0.0)

st.metric("USDC Disponible", f"{usdc:.3f}")
st.metric("XRP Disponible", f"{xrp:.3f}")

# ----------------------------------------------------
# ADD BOT
# ----------------------------------------------------
if st.button("➕ Ajouter Bot Montant-Cible"):
    st.session_state.bots.append({
        "enabled": True,
        "mode": "WAIT_AMOUNT",          # WAIT_AMOUNT → SELL → BUY → LOOP
        "target_usdc": 100.0,           # montant cible
        "sell_price": round(prix * 1.01, 5),
        "xrp_qty": 0.0,
        "gain": 0.0,
        "cycles": 0
    })
    save_bots()
    st.rerun()

# ----------------------------------------------------
# AFFICHAGE BOTS
# ----------------------------------------------------
for i, bot in enumerate(st.session_state.bots):

    st.markdown("<div class='bot'>", unsafe_allow_html=True)

    col0, col1, col2 = st.columns([1,4,4])

    # État
    if bot["mode"] == "WAIT_AMOUNT":
        col0.write("🟡")
    elif bot["mode"] == "SELL":
        col0.write("🔴")
    else:
        col0.write("🟢")

    # Montant cible USDC
    bot["target_usdc"] = col1.number_input(
        "Montant cible USDC",
        value=float(bot["target_usdc"]),
        min_value=5.0,
        key=f"target{i}"
    )

    # Prix de vente LIMIT
    bot["sell_price"] = col2.number_input(
        "Sell LIMIT à ≥",
        value=float(bot["sell_price"]),
        format="%.5f",
        key=f"sell{i}"
    )

    colA, colB, colC, colDel = st.columns([2,2,2,1])
    colA.metric("Gain total", f"{bot['gain']:.4f}")
    colB.metric("Cycles", bot["cycles"])

    if bot["enabled"]:
        if colC.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "WAIT_AMOUNT"
            bot["xrp_qty"] = 0
            save_bots()
            st.rerun()
    else:
        if colC.button("Start", key=f"start{i}"):
            bot["enabled"] = True
            bot["mode"] = "WAIT_AMOUNT"
            save_bots()
            st.rerun()

    if colDel.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# BOUCLE DE TRADING (SNOWBALL)
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
        # 1) MODE WAIT_AMOUNT → attendre que USDC >= montant cible
        # ----------------------------------------------------
        if bot["mode"] == "WAIT_AMOUNT":

            if usdc >= bot["target_usdc"]:
                bot["mode"] = "SELL"

            save_bots()
            continue

        # ----------------------------------------------------
        # 2) MODE SELL → Vente LIMIT au prix choisi
        # ----------------------------------------------------
        if bot["mode"] == "SELL":

            # quantité XRP réelle pour éviter erreurs
            sell_qty = round(xrp, 6)
            if sell_qty < 5:
                continue

            sell_price = round(bot["sell_price"], 5)

            # Coût minimum kraken 5$
            if sell_qty * sell_price < 5:
                continue

            try:
                order = exchange.create_limit_sell_order("XRP/USDC", sell_qty, sell_price)
                oid = order["id"]
            except:
                continue

            # vérifier exécution
            o = exchange.fetch_order(oid, "XRP/USDC")
            if o["status"] == "closed":

                gain = (sell_price - prix) * sell_qty
                bot["gain"] += gain
                bot["cycles"] += 1

                bot["mode"] = "BUY"
                save_bots()

        # ----------------------------------------------------
        # 3) MODE BUY → acheter tout en MARKET
        # ----------------------------------------------------
        elif bot["mode"] == "BUY":

            qty = round(usdc / prix, 6)
            if qty < 5:
                continue

            try:
                order = exchange.create_market_buy_order("XRP/USDC", qty)
            except:
                continue

            bot["xrp_qty"] = order.get("filled", qty)
            bot["mode"] = "WAIT_AMOUNT"
            save_bots()

save_bots()
