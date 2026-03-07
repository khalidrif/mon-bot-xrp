import streamlit as st
import krakenex
import streamlit.components.v1 as components

# -----------------------------
# CONFIG
# -----------------------------

st.set_page_config(layout="centered")

api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRP/USD"

# -----------------------------
# FUNCTIONS
# -----------------------------

def round_price(p):
    return float(f"{p:.5f}")

def get_price():
    try:
        data = api.query_public("Ticker", {"pair": PAIR})
        pair_key = list(data["result"].keys())[0]
        return float(data["result"][pair_key]["c"][0])
    except:
        return 0

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
# SESSION STATE
# -----------------------------

if "paliers" not in st.session_state:
    st.session_state.paliers = []

if "profit" not in st.session_state:
    st.session_state.profit = 0.0

# -----------------------------
# HEADER
# -----------------------------

st.title("XRP GRID BOT")

prix = get_price()

st.info(f"Prix XRP : {prix}")

# -----------------------------
# INPUTS
# -----------------------------

col1, col2, col3 = st.columns([1,1,1])

with col1:
    p_buy = st.number_input("BUY", value=round_price(prix - 0.02), format="%.5f")

with col2:
    p_sell = st.number_input("SELL", value=round_price(prix + 0.02), format="%.5f")

with col3:
    montant = st.number_input("USD", min_value=7.0, value=10.0)

if st.button("Ajouter Palier"):

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

# -----------------------------
# HEADER TABLE
# -----------------------------

st.markdown("`P | BUY | SELL | USD | STATE | PROFIT`")

# -----------------------------
# AFFICHAGE PALIERS
# -----------------------------

for i, p in enumerate(st.session_state.paliers):

    if not p["active"]:
        etat = "OFF"
        couleur = "#880000"

    elif p["done"]:
        etat = "DONE"
        couleur = "#660066"

    elif p["buy_id"] is None:
        etat = "WAIT BUY"
        couleur = "#00AA00"

    elif p["sell_id"] is None:
        etat = "WAIT SELL"
        couleur = "#0044AA"

    else:
        etat = "SELL"
        couleur = "#AA6600"

    components.html(f"""
    <div style='
    background:#101010;
    width:640px;
    height:38px;
    padding:4px 8px;
    margin:auto;
    margin-top:4px;
    border-radius:5px;
    border-left:4px solid {couleur};
    font-family:Consolas;
    font-size:12px;
    color:#e0e0e0;
    display:grid;
    grid-template-columns:40px 110px 110px 70px 100px 80px 60px 60px;
    align-items:center;
    '>

    <div>P{i+1}</div>

    <div style="color:#00ff88;">B:{p['buy']}</div>

    <div style="color:#ff4d4d;">S:{p['sell']}</div>

    <div>${p['usdc']}</div>

    <div>{etat}</div>

    <div style="color:#00ffaa;">+{p['gain']:.4f}</div>

    <a href='/?off={i}'>
    <button style="
    width:50px;
    height:22px;
    background:#bb0000;
    color:white;
    border:none;
    border-radius:3px;
    font-size:11px;">OFF</button>
    </a>

    <a href='/?del={i}'>
    <button style="
    width:50px;
    height:22px;
    background:#660000;
    color:white;
    border:none;
    border-radius:3px;
    font-size:11px;">DEL</button>
    </a>

    </div>
    """, height=40)

# -----------------------------
# ACTIONS URL
# -----------------------------

query = dict(st.query_params)

for key in list(query):

    if key.startswith("off"):
        idx = int(key.replace("off",""))
        st.session_state.paliers[idx]["active"] = False
        st.query_params.clear()
        st.rerun()

    if key.startswith("del"):
        idx = int(key.replace("del",""))
        st.session_state.paliers.pop(idx)
        st.query_params.clear()
        st.rerun()

# -----------------------------
# PLACER BUY
# -----------------------------

if st.button("Placer BUY"):

    for p in st.session_state.paliers:

        if p["active"] and p["buy_id"] is None:

            vol = p["usdc"] / p["buy"]

            r = place_limit("buy", p["buy"], vol)

            if not r["error"]:
                p["buy_id"] = r["result"]["txid"][0]

# -----------------------------
# SUIVI ORDRES
# -----------------------------

if st.button("Actualiser"):

    for i, p in enumerate(st.session_state.paliers):

        if not p["active"]:
            continue

        if p["buy_id"]:

            q = api.query_private("QueryOrders", {"txid": p["buy_id"]})

            if p["buy_id"] in q.get("result", {}):

                info = q["result"][p["buy_id"]]

                if info["status"] == "closed" and p["sell_id"] is None:

                    vol = p["usdc"] / p["buy"]

                    r = place_limit("sell", p["sell"], vol)

                    if "txid" in r.get("result", {}):

                        p["sell_id"] = r["result"]["txid"][0]

        if p["sell_id"]:

            q = api.query_private("QueryOrders", {"txid": p["sell_id"]})

            if p["sell_id"] in q.get("result", {}):

                info = q["result"][p["sell_id"]]

                if info["status"] == "closed" and not p["done"]:

                    gain = (p["sell"] - p["buy"]) * (p["usdc"] / p["buy"])

                    p["gain"] = gain

                    st.session_state.profit += gain

                    p["done"] = True

# -----------------------------
# PROFIT
# -----------------------------

st.markdown("---")
st.success(f"Profit total : {st.session_state.profit:.4f} USD")
