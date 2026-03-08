import streamlit as st
import krakenex
import pandas as pd

st.set_page_config(layout="wide")

# -----------------------------
# CONFIG KRAKEN
# -----------------------------
api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRPUSDC"

# -----------------------------
# FUNCTIONS
# -----------------------------
def round_price(p):
    return float(f"{p:.5f}")

def get_price():
    data = api.query_public("Ticker", {"pair": PAIR})
    return float(data["result"][PAIR]["c"][0])

# -----------------------------
# STATE
# -----------------------------
if "paliers" not in st.session_state:
    st.session_state.paliers = []

# -----------------------------
# HEADER
# -----------------------------
st.title("BOT XRP / USDC")

prix = get_price()
st.info(f"Prix actuel : {prix}")

# -----------------------------
# AJOUT PALIER
# -----------------------------
st.subheader("Ajouter un palier")

col1, col2 = st.columns(2)

with col1:
    p_buy = st.number_input(
        "BUY",
        value=round_price(prix - 0.02),
        format="%.5f"
    )

with col2:
    p_sell = st.number_input(
        "SELL",
        value=round_price(prix + 0.02),
        format="%.5f"
    )

montant = st.number_input("Montant USDC", min_value=7.0, value=10.0)

if st.button("Ajouter palier"):

    profit_estime = (p_sell - p_buy) * (montant / p_buy)

    st.session_state.paliers.append({
        "buy": p_buy,
        "sell": p_sell,
        "usdc": montant,
        "profit": profit_estime
    })

    st.success("Palier ajouté")

# -----------------------------
# TABLEAU
# -----------------------------
st.subheader("Paliers actifs")

table = []
profit_total = 0

for i, p in enumerate(st.session_state.paliers):

    profit_total += p["profit"]

    table.append({
        "Bot": i+1,
        "BUY": p["buy"],
        "SELL": p["sell"],
        "USDC": p["usdc"],
        "Profit Bot": round(p["profit"],4)
    })

df = pd.DataFrame(table)

st.dataframe(df, use_container_width=True)

# -----------------------------
# PROFIT TOTAL
# -----------------------------
st.success(f"Profit total estimé : {round(profit_total,4)} USDC")
