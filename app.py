import streamlit as st
import krakenex
import pandas as pd

st.set_page_config(layout="wide")

# -----------------------------
# CONFIG KRAKEN
# -----------------------------
api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRPUSDC"

# -----------------------------
# FUNCTIONS
# -----------------------------
def round_price(p):
    return float(f"{p:.5f}")

def get_price():
    data = api.query_public("Ticker", {"pair": PAIR})
    return float(data["result"][PAIR]["c"][0])

def place_limit(order_type, price, volume):
    price = round_price(price)
    return api.query_private("AddOrder", {
        "pair": PAIR,
        "type": order_type,
        "ordertype": "limit",
        "price": price,
        "volume": volume,
        "oflags": "post"
    })

# -----------------------------
# STATE
# -----------------------------
if "paliers" not in st.session_state:
    st.session_state.paliers = []

if "profit" not in st.session_state:
    st.session_state.profit = 0.0

# -----------------------------
# HEADER
# -----------------------------
st.title("BOT XRP / USDC")

prix = get_price()
st.info(f"Prix actuel : {prix}")

# -----------------------------
# AJOUT PALIER
# -----------------------------
st.subheader("Ajouter un palier")

col1, col2 = st.columns(2)

with col1:
    p_buy = st.number_input(
        "BUY",
        value=round_price(prix - 0.02),
        format="%.5f"
    )

with col2:
    p_sell = st.number_input(
        "SELL",
        value=round_price(prix + 0.02),
        format="%.5f"
    )

montant = st.number_input(
    "Montant USDC",
    min_value=7.0,
    value=10.0
)

if st.button("Ajouter palier"):

    st.session_state.paliers.append({
        "buy": p_buy,
        "sell": p_sell,
        "usdc": montant,
        "buy_id": None,
        "sell_id": None,
        "active": True,
        "done": False,
        "gain": 0.0
    })

    st.success("Palier ajouté")

# -----------------------------
# TABLEAU PRO
# -----------------------------
st.subheader("Paliers actifs")

table = []

for i, p in enumerate(st.session_state.paliers):

    if not p["active"]:
        etat = "OFF"

    elif p["done"]:
        etat = "FINI"

    elif p["buy_id"] is None:
        etat = "WAIT BUY"

    elif p["sell_id"] is None:
        etat = "WAIT SELL"

    else:
        etat = "EXEC SELL"

    table.append({
        "Palier": i+1,
        "BUY": p["buy"],
        "SELL": p["sell"],
        "USDC": p["usdc"],
        "Etat": etat,
        "Gain": round(p["gain"], 4)
    })

df = pd.DataFrame(table)

st.dataframe(df, use_container_width=True)

# -----------------------------
# PLACER BUY
# -----------------------------
st.subheader("Trading")

if st.button("Placer BUY"):

    for p in st.session_state.paliers:

        if p["active"] and p["buy_id"] is None:

            volume = p["usdc"] / p["buy"]

            r = place_limit("buy", p["buy"], volume)

            if not r["error"]:
                p["buy_id"] = r["result"]["txid"][0]
                st.success(f"BUY placé {p['buy']}")

            else:
                st.error(r["error"])

# -----------------------------
# PROFIT
# -----------------------------
st.write("Profit total :", round(st.session_state.profit, 4))
