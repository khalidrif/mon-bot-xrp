import streamlit as st
import krakenex
import time

# ------------------------------------------
# CONFIGURATION API
# ------------------------------------------
api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRPUSDC"

profit_net = 0.0   # gain cumulé

# ------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------
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
        "oflags": "post"  # reste visible dans Orders
    }

    res = api.query_private("AddOrder", order)
    return res


# ============================================================
#                  INTERFACE PRO AVEC GAIN NET
# ============================================================

st.markdown("""
    <h1 style='text-align:center; color:#4CAF50;'>
        BOT LIMIT TRADING – XRP/USDC (PRO)
    </h1>
""", unsafe_allow_html=True)


# ------------------------------------------
# PRIX ACTUEL
# ------------------------------------------
prix_actuel = get_price()

st.markdown(f"""
<div style="
    background-color:#1E1E1E;
    padding:20px;
    border-radius:10px;
    color:white;
    text-align:center;
    font-size:28px;
    font-weight:bold;">
    💰 Prix actuel XRP/USDC : {prix_actuel}
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# ------------------------------------------
# AFFICHAGE GAIN NET
# ------------------------------------------
if "profit" not in st.session_state:
    st.session_state.profit = 0.0

st.markdown(f"""
<div style="
    background-color:#003300;
    padding:20px;
    border-radius:10px;
    color:#00FF00;
    text-align:center;
    font-size:24px;
    font-weight:bold;">
    📊 Gain net total : {st.session_state.profit:.4f} USDC
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# ------------------------------------------
# PARAMÈTRES BUY / SELL
# ------------------------------------------
st.subheader("⚙️ Paramètres")

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

montant_usdc = st.number_input("💵 Montant USDC (min 7 USDC)", min_value=7.0, value=10.0)

st.markdown("---")


# ------------------------------------------
# ACTIONS
# ------------------------------------------
st.subheader("🟦 Actions trading")

colA, colB = st.columns(2)

with colA:
    if st.button("🟩 Envoyer LIMIT BUY"):
        montant_xrp = montant_usdc / prix_buy
        res = place_limit("buy", prix_buy, montant_xrp)

        if res["error"]:
            st.error("❌ Erreur Kraken : " + str(res["error"]))
        else:
            st.success(f"🟩 BUY créé : {montant_xrp:.4f} XRP @ {prix_buy}")

with colB:
    if st.button("🟥 Envoyer LIMIT SELL"):
        montant_xrp = montant_usdc / prix_sell
        res = place_limit("sell", prix_sell, montant_xrp)

        if res["error"]:
            st.error("❌ Erreur Kraken : " + str(res["error"]))
        else:
            st.success(f"🟥 SELL créé : {montant_xrp:.4f} XRP @ {prix_sell}")

            # Calcul du profit net
            gain = (prix_sell - prix_buy) * (montant_usdc / prix_buy)
            st.session_state.profit += gain

            st.success(f"📊 Gain ajouté : {gain:.4f} USDC")
            st.success(f"💰 Nouveau gain net total : {st.session_state.profit:.4f} USDC")

st.markdown("---")


# ------------------------------------------
# FOOTER
# ------------------------------------------
st.markdown("""
<div style='text-align:center; margin-top:30px; font-size:14px; color:#888;'>
    ⚡ Interface Trading Pro – Kraken API – LIMIT Orders visibles dans Spot Orders  
</div>
""", unsafe_allow_html=True)
