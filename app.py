import streamlit as st
import krakenex
import time

api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRPUSDC"

def round_price(p):
    return float(f"{p:.5f}")

def get_price():
    d = api.query_public("Ticker", {"pair": PAIR})
    return float(d["result"][PAIR]["c"][0])

def place_limit(order_type, price, volume):
    price = round_price(price)
    order = {
        "pair": PAIR,
        "type": order_type,
        "ordertype": "limit",
        "price": price,
        "volume": volume,
        "oflags": "post"
    }
    return api.query_private("AddOrder", order)

st.title("BOT MULTI-PALIERS (SIMPLE) – XRP/USDC LIMIT ORDERS")

prix_actuel = get_price()
st.info(f"Prix actuel : {prix_actuel}")

if "paliers" not in st.session_state:
    st.session_state.paliers = []
if "profit" not in st.session_state:
    st.session_state.profit = 0.0

st.subheader("Ajouter un palier")
col1, col2 = st.columns(2)
with col1:
    p_buy = st.number_input("Prix BUY", value=round_price(prix_actuel - 0.05), format="%.5f")
with col2:
    p_sell = st.number_input("Prix SELL", value=round_price(prix_actuel + 0.05), format="%.5f")
montant = st.number_input("Montant USDC", min_value=7.0, value=10.0)

if st.button("Ajouter ce palier"):
    st.session_state.paliers.append({
        "buy": p_buy,
        "sell": p_sell,
        "usdc": montant,
        "buy_id": None,
        "sell_id": None,
        "done": False
    })
    st.success("Palier ajouté")

st.subheader("Liste des paliers")
for i, p in enumerate(st.session_state.paliers):
    st.write(f"Palier {i+1} : BUY={p['buy']} SELL={p['sell']} USDC={p['usdc']}")

if st.button("Démarrer les ordres BUY"):
    for p in st.session_state.paliers:
        vol = p["usdc"] / p["buy"]
        res = place_limit("buy", p["buy"], vol)
        if not res["error"]:
            p["buy_id"] = res["result"]["txid"][0]
            st.success(f"BUY placé pour palier : {p['buy']}")

st.markdown("---")
st.subheader("Suivi des ordres")

if st.button("Actualiser"):
    for p in st.session_state.paliers:
        # Vérifier BUY exécuté
        if p["buy_id"]:
            q = api.query_private("QueryOrders", {"txid": p["buy_id"]})
            info = q["result"][p["buy_id"]]
            if info["status"] == "closed" and not p["sell_id"]:
                vol = p["usdc"] / p["buy"]
                res = place_limit("sell", p["sell"], vol)
                if not res["error"]:
                    p["sell_id"] = res["result"]["txid"][0]
                    st.success(f"SELL créé pour palier BUY={p['buy']}")

        # Vérifier SELL exécuté
        if p["sell_id"]:
            q = api.query_private("QueryOrders", {"txid": p["sell_id"]})
            info = q["result"][p["sell_id"]]
            if info["status"] == "closed" and not p["done"]:
                gain = (p["sell"] - p["buy"]) * (p["usdc"] / p["buy"])
                st.session_state.profit += gain
                p["done"] = True
                st.success(f"Palier terminé : gain {gain:.4f} USDC")

st.info(f"Gain total : {st.session_state.profit:.4f} USDC")
