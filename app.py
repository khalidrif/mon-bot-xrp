import streamlit as st
import krakenex
import streamlit.components.v1 as components

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

def cancel_order(order_id):
    return api.query_private("CancelOrder", {"txid": order_id})

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
st.title("BOT XRP/USDC – MULTI-PALIERS (SUPER PRO FINAL)")

prix = get_price()
st.info(f"Prix actuel XRP/USDC : {prix}")

# -------------------------------------
# AJOUT PALIER
# -------------------------------------
st.subheader("➕ Ajouter un palier")

col1, col2 = st.columns(2)
with col1:
    p_buy = st.number_input("BUY", value=round_price(prix - 0.02), format="%.5f")
with col2:
    p_sell = st.number_input("SELL", value=round_price(prix + 0.02), format="%.5f")

montant = st.number_input("Montant USDC (min 7)", min_value=7.0, value=10.0)

if st.button("Ajouter"):
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
    st.success("Palier ajouté ✔")

# -------------------------------------
# AFFICHAGE PALIERS SUPER PRO
# -------------------------------------
st.subheader("📋 Paliers (SUPER PRO)")

for i, p in enumerate(st.session_state.paliers):

    # Fix keys
    for k, v in {
        "active": True,
        "done": False,
        "gain": 0.0,
        "buy_id": None,
        "sell_id": None,
    }.items():
        if k not in p:
            p[k] = v

    # Déterminer l'état + couleur
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

    # BANDE SUPER PRO (alignement terminal)
    components.html(f"""
    <div style='
        background-color:#101010;
        padding:6px 10px;
        margin-top:6px;
        border-radius:6px;
        border-left:6px solid {couleur};
        font-family:Consolas, monospace;
        font-size:14px;
        color:white;
        display:flex;
        justify-content:space-between;
        align-items:center;
    '>

        <div style='
            display:grid;
            grid-template-columns: 60px 150px 150px 120px 150px 130px;
            column-gap:15px;
            align-items:center;
        '>
            <div>P{i+1}</div>
            <div>BUY:{p['buy']}</div>
            <div>SELL:{p['sell']}</div>
            <div>{p['usdc']} USDC</div>
            <div>{etat}</div>
            <div>Gain:{p['gain']:.4f}</div>
        </div>

        <div style='display:flex; gap:10px;'>

            <a href='/?off={i}'>
                <button style='
                    padding:3px 12px;
                    background:#bb0000;
                    color:white;
                    border:none;
                    border-radius:4px;
                    font-family:Consolas, monospace;
                '>OFF</button>
            </a>

            <a href='/?del={i}'>
                <button style='
                    padding:3px 12px;
                    background:#660000;
                    color:white;
                    border:none;
                    border-radius:4px;
                    font-family:Consolas, monospace;
                '>DEL</button>
            </a>

        </div>

    </div>
    """, height=55)

# -------------------------------------
# TRAITEMENT DES ACTIONS URL
# -------------------------------------
query = st.query_params

for key in list(query):

    # OFF
    if key.startswith("off"):
        idx = int(key.replace("off", ""))
        st.session_state.paliers[idx]["active"] = False
        st.query_params.clear()
        st.rerun()

    # DEL
    if key.startswith("del"):
        idx = int(key.replace("del", ""))
        st.session_state.paliers.pop(idx)
        st.query_params.clear()
        st.rerun()

# -------------------------------------
# PLACER TOUS LES BUY
# -------------------------------------
st.subheader("🚀 Placer BUY actifs")

if st.button("Placer BUY"):
    for p in st.session_state.paliers:
        if p["active"] and p["buy_id"] is None:
            vol = p["usdc"] / p["buy"]
            r = place_limit("buy", p["buy"], vol)
            if not r["error"]:
                p["buy_id"] = r["result"]["txid"][0]
                st.success(f"BUY placé {p['buy']}")
            else:
                st.error(str(r["error"]))

# -------------------------------------
# SUIVI ORDRES BUY / SELL
# -------------------------------------
st.subheader("📡 Suivi")

if st.button("Actualiser"):
    for i, p in enumerate(st.session_state.paliers):

        if not p["active"]:
            continue

        # BUY exécuté → placer SELL
        if p["buy_id"]:
            q = api.query_private("QueryOrders", {"txid": p["buy_id"]})
            info = q["result"][p["buy_id"]]
            if info["status"] == "closed" and p["sell_id"] is None:
                vol = p["usdc"] / p["buy"]
                r = place_limit("sell", p["sell"], vol)
                if "txid" in r.get("result", {}):
                    p["sell_id"] = r["result"]["txid"][0]
                    st.success(f"SELL placé {p['sell']}")

        # SELL exécuté → gain
        if p["sell_id"]:
            q = api.query_private("QueryOrders", {"txid": p["sell_id"]})
            info = q["result"][p["sell_id"]]
            if info["status"] == "closed" and not p["done"]:
                gain = (p["sell"] - p["buy"]) * (p["usdc"] / p["buy"])
                p["gain"] = gain
                st.session_state.profit += gain
                p["done"] = True
                st.success(f"Gain P{i+1} = {gain:.4f}")

# -------------------------------------
# TOTAL GAIN
# -------------------------------------
st.markdown("---")
st.info(f"💰 Gain total : {st.session_state.profit:.4f} USDC")
