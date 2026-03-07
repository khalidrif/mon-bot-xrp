import streamlit as st
import streamlit.components.v1 as components
import krakenex

# -------------------------------------
# CONFIG KRAKEN
# -------------------------------------

api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRPUSDC"

# -------------------------------------
# FUNCTIONS
# -------------------------------------

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

# -------------------------------------
# STATE
# -------------------------------------

if "paliers" not in st.session_state:
    st.session_state.paliers = []

if "profit" not in st.session_state:
    st.session_state.profit = 0.0

# -------------------------------------
# HEADER
# -------------------------------------

st.title("BOT XRP/USDC – MULTI PALIERS")

prix = get_price()

st.info(f"Prix XRP/USDC : {prix}")

# -------------------------------------
# AJOUT PALIER
# -------------------------------------

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

# -------------------------------------
# AFFICHAGE PALIERS
# -------------------------------------

st.subheader("Paliers")

for i, p in enumerate(st.session_state.paliers):

    if not p["active"]:
        etat = "OFF"
        couleur = "#880000"

    elif p["done"]:
        etat = "FINI"
        couleur = "#660066"

    elif p["buy_id"] is None:
        etat = "WAIT BUY"
        couleur = "#00AA00"

    elif p["sell_id"] is None:
        etat = "WAIT SELL"
        couleur = "#0044AA"

    else:
        etat = "EXEC SELL"
        couleur = "#AA6600"

    components.html(f"""
    <div style='
        background:#101010;
        padding:6px;
        margin-top:6px;
        border-radius:6px;
        border-left:6px solid {couleur};
        font-family:Consolas;
        color:white;
        display:flex;
        justify-content:space-between;
        align-items:center;
    '>

        <div>
        P{i+1} | 
        BUY <span style="color:#00ff88">{p['buy']}</span> |
        SELL <span style="color:#ff4d4d">{p['sell']}</span> |
        {p['usdc']} USDC |
        {etat} |
        Gain {p['gain']:.4f}
        </div>

    </div>
    """, height=40)

# -------------------------------------
# PLACER BUY
# -------------------------------------

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

# -------------------------------------
# PROFIT
# -------------------------------------

st.write("Profit total :", st.session_state.profit)
