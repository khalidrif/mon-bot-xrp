import streamlit as st
import krakenex
import streamlit.components.v1 as components

# -------------------------------------
# CONFIG
# -------------------------------------

st.set_page_config(layout="centered")

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

st.title("BOT XRP/USDC – GRID TRADING")

prix = get_price()
st.info(f"Prix actuel XRP/USDC : {prix}")

# -------------------------------------
# AJOUT PALIER
# -------------------------------------

st.subheader("Ajouter un palier")

col1, col2 = st.columns(2)

with col1:
    p_buy = st.number_input("BUY", value=round_price(prix - 0.02), format="%.5f")

with col2:
    p_sell = st.number_input("SELL", value=round_price(prix + 0.02), format="%.5f")

montant = st.number_input("Montant USDC", min_value=7.0, value=10.0)

if st.button("Ajouter Palier"):
    st.session_state.paliers.append({
        "buy": p_buy,
        "sell": p_sell,
        "usdc": montant,
        "buy_id": None,
        "sell_id": None,
        "active": True,
        "done": False,
        "gain": 0.0,
    })
    st.success("Palier ajouté")

# -------------------------------------
# LISTE PALIERS
# -------------------------------------

st.subheader("Paliers actifs")

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
width:100%;
max-width:390px;
padding:10px;
margin:auto;
margin-top:8px;
border-radius:10px;
border-left:6px solid {couleur};
font-family:Consolas, monospace;
font-size:13px;
color:white;
display:flex;
flex-direction:column;
gap:6px;
'>

<div style='display:flex; justify-content:space-between;'>
<div>P{i+1}</div>
<div>{etat}</div>
</div>

<div style='display:flex; justify-content:space-between;'>
<div style="color:#00ff88;">BUY</div>
<div style="color:#00ff88;">{p['buy']}</div>
</div>

<div style='display:flex; justify-content:space-between;'>
<div style="color:#ff4d4d;">SELL</div>
<div style="color:#ff4d4d;">{p['sell']}</div>
</div>

<div style='display:flex; justify-content:space-between;'>
<div>MONTANT</div>
<div>{p['usdc']} USDC</div>
</div>

<div style='display:flex; justify-content:space-between;'>
<div>GAIN</div>
<div>{p['gain']:.4f}</div>
</div>

<div style='display:flex; gap:8px; margin-top:6px;'>

<a href='/?off={i}' style='flex:1;'>
<button style='
width:100%;
padding:6px;
background:#bb0000;
color:white;
border:none;
border-radius:6px;
font-family:Consolas;
'>OFF</button>
</a>

<a href='/?del={i}' style='flex:1;'>
<button style='
width:100%;
padding:6px;
background:#660000;
color:white;
border:none;
border-radius:6px;
font-family:Consolas;
'>DEL</button>
</a>

</div>

</div>
""", height=170)

# -------------------------------------
# ACTIONS URL
# -------------------------------------

query = st.query_params

for key in list(query):

    if key.startswith("off"):
        idx = int(key.replace("off", ""))
        st.session_state.paliers[idx]["active"] = False
        st.query_params.clear()
        st.rerun()

    if key.startswith("del"):
        idx = int(key.replace("del", ""))
        st.session_state.paliers.pop(idx)
        st.query_params.clear()
        st.rerun()

# -------------------------------------
# PLACER BUY
# -------------------------------------

st.subheader("Placer BUY")

if st.button("Placer BUY actifs"):

    for p in st.session_state.paliers:

        if p["active"] and p["buy_id"] is None:

            volume = p["usdc"] / p["buy"]

            r = place_limit("buy", p["buy"], volume)

            if not r["error"]:

                p["buy_id"] = r["result"]["txid"][0]

                st.success(f"BUY placé {p['buy']}")

            else:

                st.error(str(r["error"]))

# -------------------------------------
# SUIVI ORDRES
# -------------------------------------

st.subheader("Suivi ordres")

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

                        st.success(f"SELL placé {p['sell']}")

        if p["sell_id"]:

            q = api.query_private("QueryOrders", {"txid": p["sell_id"]})

            if p["sell_id"] in q.get("result", {}):

                info = q["result"][p["sell_id"]]

                if info["status"] == "closed" and not p["done"]:

                    gain = (p["sell"] - p["buy"]) * (p["usdc"] / p["buy"])

                    p["gain"] = gain

                    st.session_state.profit += gain

                    p["done"] = True

                    st.success(f"Gain P{i+1} = {gain:.4f}")

# -------------------------------------
# PROFIT TOTAL
# -------------------------------------

st.markdown("---")

st.info(f"Gain total : {st.session_state.profit:.4f} USDC")
