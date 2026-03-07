import streamlit as st
import krakenex
import time
import pandas as pd
import streamlit.components.v1 as components

# ---------------------------------------
# CONFIG KRAKEN API
# ---------------------------------------
api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]
PAIR = "XRPUSDC"


# ---------------------------------------
# FONCTIONS UTILITAIRES
# ---------------------------------------
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
        "oflags": "post"      # IMPORTANT pour être visible dans Kraken
    }
    return api.query_private("AddOrder", order)

def cancel_order(order_id):
    return api.query_private("CancelOrder", {"txid": order_id})


# ---------------------------------------
# STREAMLIT STATE
# ---------------------------------------
if "paliers" not in st.session_state:
    st.session_state.paliers = []

if "profit" not in st.session_state:
    st.session_state.profit = 0.0


# ---------------------------------------
# UI - PRIX ACTUEL
# ---------------------------------------
st.title("BOT LIMIT XRP/USDC – MULTI-PALIERS (PRO)")

prix_actuel = get_price()
st.info(f"💰 Prix actuel XRP/USDC : {prix_actuel}")


# ---------------------------------------
# AJOUT D’UN NOUVEAU PALIER
# ---------------------------------------
st.subheader("➕ Ajouter un palier")

col1, col2 = st.columns(2)
with col1:
    p_buy = st.number_input("Prix BUY", value=round_price(prix_actuel - 0.05), format="%.5f")
with col2:
    p_sell = st.number_input("Prix SELL", value=round_price(prix_actuel + 0.05), format="%.5f")

montant = st.number_input("Montant USDC (min 7 USDC)", min_value=7.0, value=10.0)

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


# ---------------------------------------
# AFFICHAGE PALIERS (PRO)
# ---------------------------------------
st.subheader("📋 Liste des paliers (mode PRO)")

if len(st.session_state.paliers) == 0:
    st.warning("Aucun palier ajouté.")
else:
    for i, p in enumerate(st.session_state.paliers):

        # ==== ÉTAT DU PALIER ====
        if not p["active"]:
            etat = "🔴 Palier désactivé"
            couleur = "#880000"
        elif p["done"]:
            etat = "🟣 Cycle terminé"
            couleur = "#6A0DAD"
        elif p["buy_id"] is None:
            etat = "🟢 En attente BUY"
            couleur = "#00AA00"
        elif p["sell_id"] is None:
            etat = "🔵 BUY exécuté → attente SELL"
            couleur = "#0066FF"
        else:
            etat = "🟠 SELL placé → attente exécution"
            couleur = "#FF8800"

        # ==== BANDE PRO ====
        components.html(f"""
        <div style='
            background-color:#1A1A1A;
            padding:15px;
            margin-top:20px;
            border-radius:10px;
            border-left:10px solid {couleur};
            color:white;
            font-family:Arial;
        '>
            <h3 style="margin:0;">Palier P{i+1}</h3>

            <p style="margin:6px 0; font-size:16px;">
                <span style="color:#00FF00; font-weight:bold;">BUY : {p['buy']}</span>
                →
                <span style="color:#FF4444; font-weight:bold;">SELL : {p['sell']}</span><br>
                💵 Montant : <b>{p['usdc']} USDC</b><br>
                🔁 État : <b>{etat}</b><br>
                📈 Gain palier : <b>{p['gain']:.4f} USDC</b>
            </p>
        </div>
        """, height=170)

        # ==== BOUTONS ====
        colA, colB, colC, colD, colE = st.columns(5)

        # ACTIVER
        with colA:
            if not p["active"]:
                if st.button(f"🟢 ON", key=f"on_{i}"):
                    p["active"] = True
                    st.experimental_rerun()

        # DESACTIVER
        with colB:
            if p["active"]:
                if st.button(f"🔴 OFF", key=f"off_{i}"):
                    p["active"] = False
                    st.experimental_rerun()

        # ANNULER BUY
        with colC:
            if p["buy_id"]:
                if st.button(f"❌ BUY", key=f"cancel_buy_{i}"):
                    cancel_order(p["buy_id"])
                    p["buy_id"] = None
                    st.experimental_rerun()

        # ANNULER SELL
        with colD:
            if p["sell_id"]:
                if st.button(f"❌ SELL", key=f"cancel_sell_{i}"):
                    cancel_order(p["sell_id"])
                    p["sell_id"] = None
                    st.experimental_rerun()

        # SUPPRIMER PALIER
        with colE:
            if st.button(f"🗑️ DEL", key=f"del_{i}"):
                st.session_state.paliers.pop(i)
                st.experimental_rerun()


# ---------------------------------------
# ANNULER TOUS LES ORDRES
# ---------------------------------------
st.subheader("🛑 Annuler TOUS les ordres Kraken")

if st.button("Annuler tous les ordres Kraken"):
    res = api.query_private("CancelAll")
    st.warning(res)
    for p in st.session_state.paliers:
        p["buy_id"] = None
        p["sell_id"] = None
    st.success("Tous les ordres ont été réinitialisés locally.")


# ---------------------------------------
# ENVOYER LES BUY
# ---------------------------------------
st.markdown("---")
st.subheader("🚀 Placer tous les BUY actifs")

if st.button("Placer LIMIT BUY"):
    for p in st.session_state.paliers:
        if not p["active"]:
            continue
        if p["buy_id"] is None:
            vol = p["usdc"] / p["buy"]
            r = place_limit("buy", p["buy"], vol)
            if not r["error"]:
                p["buy_id"] = r["result"]["txid"][0]
                st.success(f"BUY placé : {p['buy']}")
            else:
                st.error(str(r["error"]))


# ---------------------------------------
# SUIVI DES ORDRES
# ---------------------------------------
st.markdown("---")
st.subheader("📡 Suivi des cycles")

if st.button("Actualiser"):
    for p in st.session_state.paliers:

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
                    st.success(f"SELL placé : {p['sell']}")

        # SELL exécuté
        if p["sell_id"]:
            q = api.query_private("QueryOrders", {"txid": p["sell_id"]})
            info = q["result"][p["sell_id"]]

            if info["status"] == "closed" and not p["done"]:
                gain = (p["sell"] - p["buy"]) * (p["usdc"] / p["buy"])
                p["gain"] = gain
                st.session_state.profit += gain
                p["done"] = True
                st.success(f"Gain palier P{i+1} = {gain:.4f} USDC")


# ---------------------------------------
# GAIN TOTAL
# ---------------------------------------
st.markdown("---")
st.info(f"💰 Gain total : {st.session_state.profit:.4f} USDC")
