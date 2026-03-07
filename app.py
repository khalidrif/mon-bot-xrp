import streamlit as st
import krakenex
import time

# -------------------------------
# CONFIG API
# -------------------------------
api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]
PAIR = "XRPUSDC"

# -------------------------------
# HELPERS
# -------------------------------
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
    res = api.query_private("AddOrder", order)
    return res


# ============================================================
#                INTERFACE PRO – STYLE TRADING
# ============================================================

st.markdown("""
    <h1 style='text-align:center; color:#4CAF50;'>
        BOT LIMIT TRADING – XRP/USDC
    </h1>
""", unsafe_allow_html=True)

# --- Prix actuel
prix_actuel = get_price()

st.markdown("""
<div style="
    background-color:#1E1E1E;
    padding:20px;
    border-radius:10px;
    color:white;
    text-align:center;
    font-size:28px;
    font-weight:bold;">
    💰 Prix actuel XRP/USDC : {} 
</div>
""".format(prix_actuel), unsafe_allow_html=True)

st.markdown("---")


# ================================
#        Paramètres du trade
# ================================
st.subheader("⚙️ Paramètres du Limit Order")

col1, col2 = st.columns(2)

with col1:
    prix_buy = st.number_input(
        "🎯 Prix LIMIT BUY",
        value=round_price(prix_actuel - 0.05),
        format="%.5f"
    )

with col2:
    prix_sell = st.number_input(
        "📈 Prix LIMIT SELL",
        value=round_price(prix_actuel + 0.05),
        format="%.5f"
    )

montant_usdc = st.number_input(
    "💵 Montant USDC (min 7 USDC)",
    min_value=7.0,
    value=10.0
)

st.markdown("---")


# ================================
#       Boutons d'action
# ================================
st.subheader("🟦 Actions")

colA, colB = st.columns(2)

with colA:
    if st.button("🟩 Envoyer LIMIT BUY"):
        montant_xrp = montant_usdc / prix_buy
        res = place_limit("buy", prix_buy, montant_xrp)

        if res["error"]:
            st.error("❌ Erreur Kraken : " + str(res["error"]))
        else:
            st.success(f"🟩 LIMIT BUY créé : {montant_xrp:.4f} XRP @ {prix_buy}")

with colB:
    if st.button("🟥 Envoyer LIMIT SELL"):
        montant_xrp = montant_usdc / prix_sell
        res = place_limit("sell", prix_sell, montant_xrp)

        if res["error"]:
            st.error("❌ Erreur Kraken : " + str(res["error"]))
        else:
            st.success(f"🟥 LIMIT SELL créé : {montant_xrp:.4f} XRP @ {prix_sell}")

st.markdown("---")


# ================================
#        Footer pro
# ================================
st.markdown("""
<div style='text-align:center; margin-top:30px; font-size:14px; color:#7F7F7F;'>
    ⚡ Interface trading professionnelle – Kraken API – LIMIT Orders visibles dans Spot Orders  
</div>
""", unsafe_allow_html=True)
