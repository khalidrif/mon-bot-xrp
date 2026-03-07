import streamlit as st
import krakenex
import pandas as pd
import streamlit.components.v1 as components

# ------------------------------
# KRAKEN CONFIG
# ------------------------------
api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]
PAIR = "XRPUSDC"


# ------------------------------
# FUNCTIONS
# ------------------------------
def round_price(p):
    return float(f"{p:.5f}")

def get_price():
    d = api.query_public("Ticker", {"pair": PAIR})
    return float(d["result"][PAIR]["c"][0])

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


# ------------------------------
# STREAMLIT STATE
# ------------------------------
if "paliers" not in st.session_state:
    st.session_state.paliers = []

if "profit" not in st.session_state:
    st.session_state.profit = 0.0


# ------------------------------
# PRIX ACTUEL
# ------------------------------
st.title("BOT XRP/USDC – MULTI-PALIERS (PRO, FINAL)")
prix_actuel = get_price()
st.info(f"💰 Prix actuel : {prix_actuel}")


# ------------------------------
# AJOUT PALIER
# ------------------------------
st.subheader("➕ Ajouter un palier")

col1, col2 = st.columns(2)

with col1:
    p_buy = st.number_input("Prix BUY", value=round_price(prix_actuel - 0.02), format="%.5f")
with col2:
    p_sell = st.number_input("Prix SELL", value=round_price(prix_actuel + 0.02), format="%.5f")

montant = st.number_input("Montant USDC (min 7)", min_value=7.0, value=10.0)

if st.button("Ajouter ce palier"):
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
    st.success("Palier ajouté !")


# ------------------------------
# AFFICHAGE PALIERS (1 LIGNE)
# ------------------------------
st.subheader("📋 Paliers")

for i, p in enumerate(st.session_state.paliers):

    # Fix keys if missing
    for k, v in {
        "active": True, "done": False, "gain": 0.0,
        "buy_id": None, "sell_id": None
    }.items():
        if k not in p:
            p[k] = v

    # Etat + couleur
    if not p["active"]:
        etat = "🔴 OFF"
        couleur = "#880000"
    elif p["done"]:
        etat = "🟣 FINI"
        couleur = "#551177"
    elif p["buy_id"] is None:
        etat = "🟢 WAIT BUY"
        couleur = "#00AA00"
    elif p["sell_id"] is None:
        etat = "🔵 WAIT SELL"
        couleur = "#0044AA"
    else:
        etat = "🟠 EXEC SELL"
        couleur = "#AA6600"

    # BANDE HORIZONTALE
    components.html(f"""
    <div style='
        display:flex;
        justify-content:space-between;
        align-items:center;
        background-color:#1A1A1A;
        padding:10px;
        margin-top:10px;
        border-radius:8px;
        border-left:10px solid {couleur};
        color:white;
        font-family:Arial;
        font-size:14px;
    '>

        <div style='display:flex; gap:20px;'>
            <div><b>P{i+1}</b></div>
            <div style='color:#00FF00; font-weight:bold;'>BUY {p['buy']}</div>
            <div style='color:#FF5555; font-weight:bold;'>SELL {p['sell']}</div>
            <div>💵 {p['usdc']} USDC</div>
            <div>🔁 {etat}</div>
            <div>📈 {p['gain']:.4f} USDC</div>
        </div>

        <div style='display:flex; gap:10px;'>

            <a href='/?off={i}'>
                <button style='padding:4px 10px;'>🔴 OFF</button>
            </a>

            <a href='/?del={i}'>
                <button style='padding:4px 10px; background:#AA0000; color:white;'>🗑️ DEL</button>
            </a>

        </div>

    </div>
    """, height=65)

# ------------------------------
# ACTIONS VIA URL
# ------------------------------
query = st.experimental_get_query_params()

for key in query:

    # Désactiver
    if key.startswith("off"):
        idx = int(key.replace("off", ""))
        st.session_state.paliers[idx]["active"] = False
        st.experimental_set_query_params()
        st.experimental_rerun()

    # Supprimer
    if key.startswith("del"):
        idx = int(key.replace("del", ""))
        st.session_state.paliers.pop(idx)
        st.experimental_set_query_params()
        st.experimental_rerun()


# ------------------------------
# BOUTON PLACER TOUS LES BUY
# ------------------------------
st.subheader("🚀 Placer tous les BUY actifs")

if st.button("Placer LIMIT BUY"):
    for p in st.session_state.paliers:
        if p["active"] and p["buy_id"] is None:
            vol = p["usdc"] / p["buy"]
            res = place_limit("buy", p["buy"], vol)
            if not res["error"]:
                p["buy_id"] = res["result"]["txid"][0]
                st.success(f"BUY placé {p['buy']}")
            else:
                st.error(str(res["error"]))


# ------------------------------
# SUIVI DES ORDRES
# ------------------------------
st.subheader("📡 Suivi")

if st.button("Actualiser"):
    for i, p in enumerate(st.session_state.paliers):

        if not p["active"]:
            continue

        # BUY exécuté
        if p["buy_id"]:
            q = api.query_private("QueryOrders", {"txid": p["buy_id"]})
            info = q["result"][p["buy_id"]]
            if info["status"] == "closed" and p["sell_id"] is None:
                vol = p["usdc"] / p["buy"]
                r = place_limit("sell", p["sell"], vol)
                if not r["error"]:
                    p["sell_id"] = r["result"]["txid"][0]
                    st.success(f"SELL placé {p['sell']}")

        # SELL exécuté
        if p["sell_id"]:
            q = api.query_private("QueryOrders", {"txid": p["sell_id"]})
            info = q["result"][p["sell_id"]]
            if info["status"] == "closed" and not p["done"]:
                gain = (p["sell"] - p["buy"]) * (p["usdc"] / p["buy"])
                p["gain"] = gain
                st.session_state.profit += gain
                p["done"] = True
                st.success(f"Gain P{i+1} = {gain:.4f} USDC")


# ------------------------------
# GAIN TOTAL
# ------------------------------
st.markdown("---")
st.info(f"💰 Gain total : {st.session_state.profit:.4f} USDC")
