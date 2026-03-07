import streamlit as st
import krakenex
import streamlit.components.v1 as components

# -------------------------------
# CONFIG
# -------------------------------

st.set_page_config(layout="centered")

api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRP/USD"

# -------------------------------
# FUNCTIONS
# -------------------------------

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

# -------------------------------
# STATE
# -------------------------------

if "paliers" not in st.session_state:
    st.session_state.paliers = []

if "profit" not in st.session_state:
    st.session_state.profit = 0.0

# -------------------------------
# HEADER
# -------------------------------

st.title("BOT XRP GRID")

prix = get_price()
st.info(f"Prix actuel XRP : {prix}")

# -------------------------------
# AJOUT PALIER
# -------------------------------

col1, col2 = st.columns(2)

with col1:
    p_buy = st.number_input("BUY", value=round_price(prix - 0.02), format="%.5f")

with col2:
    p_sell = st.number_input("SELL", value=round_price(prix + 0.02), format="%.5f")

montant = st.number_input("Montant USD", min_value=7.0, value=10.0)

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

# -------------------------------
# AFFICHAGE PALIERS
# -------------------------------

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
    width:100%;
    max-width:390px;
    padding:5px;
    margin:auto;
    margin-top:6px;
    border-radius:6px;
    border-left:4px solid {couleur};
    font-family:Consolas;
    font-size:12px;
    color:white;
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:6px;
    '>

    <div>P{i+1}</div>

    <div style="color:#00ff88;">BUY {p['buy']}</div>

    <div style="color:#ff4d4d;">SELL {p['sell']}</div>

    <div>{p['usdc']}$</div>

    <div>{etat}</div>

    <div>G:{p['gain']:.4f}</div>

    <div style="display:flex;gap:4px">

    <a href='/?off={i}'>
    <button style="padding:2px 6px;background:#bb0000;color:white;border:none;border-radius:4px;font-size:11px">OFF</button>
    </a>

    <a href='/?del={i}'>
    <button style="padding:2px 6px;background:#660000;color:white;border:none;border-radius:4px;font-size:11px">DEL</button>
    </a>

    </div>

    </div>
    """, height=40)

# -------------------------------
# URL ACTIONS
# -------------------------------

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

# -------------------------------
# PLACER BUY
# -------------------------------

if st.button("Placer BUY"):

    for p in st.session_state.paliers:

        if p["active"] and p["buy_id"] is None:

            vol = p["usdc"] / p["buy"]

            r = place_limit("buy", p["buy"], vol)

            if not r["error"]:
                p["buy_id"] = r["result"]["txid"][0]

# -------------------------------
# SUIVI ORDRES
# -------------------------------

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

# -------------------------------
# PROFIT
# -------------------------------

st.markdown("---")
st.info(f"Profit total : {st.session_state.profit:.4f} USD")
