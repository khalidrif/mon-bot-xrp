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

def cancel_order(oid):
    return api.query_private("CancelOrder", {"txid": oid})

# -------------------------------------
# STATE
# -------------------------------------
if "paliers" not in st.session_state:
    st.session_state.paliers = []
if "profit" not in st.session_state:
    st.session_state.profit = 0.0

# -------------------------------------
# UI HEADER
# -------------------------------------
st.title("BOT XRP/USDC — MULTI-PALIERS (FINAL TABLEAU SIMPLE)")
prix = get_price()
st.info(f"Prix actuel XRP/USDC : {prix}")

# -------------------------------------
# ADD PALIER
# -------------------------------------
st.subheader("Ajouter un palier")

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
    st.success("Palier ajouté")

# -------------------------------------
# DISPLAY PALIERS (TABLEAU SIMPLE)
# -------------------------------------
st.subheader("Paliers")

if len(st.session_state.paliers) == 0:
    st.warning("Aucun palier.")
else:
    for i, p in enumerate(st.session_state.paliers):

        # corriger clés manquantes
        for k, v in {
            "active": True, "done": False, "gain": 0.0,
            "buy_id": None, "sell_id": None
        }.items():
            if k not in p:
                p[k] = v

        components.html(f"""
        <table style='width:100%; border-collapse:collapse; font-family:Arial;'>
            <tr style='background:#111; color:white; font-size:14px;'>
                <td style='padding:6px; text-align:center;'>{'P'+str(i+1)}</td>
                <td style='padding:6px; text-align:center;'>{p['buy']}</td>
                <td style='padding:6px; text-align:center;'>{p['sell']}</td>
                <td style='padding:6px; text-align:center;'>{p['usdc']} USDC</td>

                <td style='padding:6px; text-align:center;'>
                    <a href='/?off={i}'>
                        <button style='padding:4px 12px;'>OFF</button>
                    </a>
                </td>

                <td style='padding:6px; text-align:center;'>
                    <a href='/?del={i}'>
                        <button style='padding:4px 12px; background:#AA0000; color:white;'>DEL</button>
                    </a>
                </td>
            </tr>
        </table>
        """, height=45)

# -------------------------------------
# URL ACTIONS : OFF / DEL
# -------------------------------------
query = st.query_params

for key in list(query):

    # Désactiver
    if key.startswith("off"):
        idx = int(key.replace("off",""))
        st.session_state.paliers[idx]["active"] = False
        st.query_params.clear()
        st.rerun()

    # Supprimer
    if key.startswith("del"):
        idx = int(key.replace("del",""))
        st.session_state.paliers.pop(idx)
        st.query_params.clear()
        st.rerun()

# -------------------------------------
# SEND ALL BUY
# -------------------------------------
st.subheader("Placer BUY")

if st.button("Placer tous les BUY actifs"):
    for p in st.session_state.paliers:
        if p["active"] and p["buy_id"] is None:
            vol = p["usdc"] / p["buy"]
            r = place_limit("buy", p["buy"], vol)
            if not r["error"]:
                p["buy_id"] = r["result"]["txid"][0]
                st.success(f"BUY placé : {p['buy']}")
            else:
                st.error(str(r["error"]))

# -------------------------------------
# FOLLOW ORDERS
# -------------------------------------
st.subheader("Suivi")

if st.button("Actualiser"):
    for i, p in enumerate(st.session_state.paliers):

        if not p["active"]:
            continue

        # BUY effectué
        if p["buy_id"]:
            q = api.query_private("QueryOrders", {"txid": p["buy_id"]})
            info = q["result"][p["buy_id"]]
            if info["status"] == "closed" and p["sell_id"] is None:
                vol = p["usdc"] / p["buy"]
                r = place_limit("sell", p["sell"], vol)
                if "txid" in r.get("result", {}):
                    p["sell_id"] = r["result"]["txid"][0]
                    st.success(f"SELL placé : {p['sell']}")

        # SELL effectué
        if p["sell_id"]:
            q = api.query_private("QueryOrders", {"txid": p["sell_id"]})
            info = q["result"][p["sell_id"]]
            if info["status"] == "closed" and not p["done"]:
                gain = (p["sell"] - p["buy"]) * (p["usdc"] / p["buy"])
                p["gain"] = gain
                p["done"] = True
                st.session_state.profit += gain
                st.success(f"Gain P{i+1} = {gain:.4f} USDC")

# -------------------------------------
# TOTAL GAIN
# -------------------------------------
st.markdown("---")
st.info(f"Gain total : {st.session_state.profit:.4f} USDC")
