import streamlit as st
import pandas as pd

st.set_page_config(page_title="XRP Bot", layout="wide")

st.title("🤖 XRP Trading Bot")

# -------------------------
# Initialisation
# -------------------------

if "paliers" not in st.session_state:
    st.session_state.paliers = []

# -------------------------
# Style simple
# -------------------------

st.markdown("""
<style>
.stNumberInput input{
height:45px;
font-size:18px;
border-radius:10px;
border:1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Prix XRP
# -------------------------

prix = st.number_input("Prix XRP", value=1.34, step=0.001)

st.write("Prix actuel :", prix)

# -------------------------
# Ajouter bot
# -------------------------

st.subheader("➕ Ajouter un Bot")

col1,col2,col3,col4 = st.columns(4)

with col1:
    buy = st.number_input("BUY", value=1.33)

with col2:
    sell = st.number_input("SELL", value=1.37)

with col3:
    usdc = st.number_input("USDC", value=10.0)

with col4:
    if st.button("Ajouter Bot"):
        st.session_state.paliers.append({
            "buy": buy,
            "sell": sell,
            "usdc": usdc,
            "buy_done": False
        })

# -------------------------
# Logique bot
# -------------------------

for p in st.session_state.paliers:

    if not p["buy_done"] and prix <= p["buy"]:
        p["buy_done"] = True

    if p["buy_done"] and prix >= p["sell"]:
        p["buy_done"] = False

# -------------------------
# Tableau bots
# -------------------------

table = []
profit_total = 0

for i,p in enumerate(st.session_state.paliers):

    profit = (p["sell"] - p["buy"]) * (p["usdc"] / p["buy"])
    profit_total += profit

    buy_display = "🟢 " + str(p["buy"]) if p["buy_done"] else str(p["buy"])

    table.append({
        "Bot": i+1,
        "BUY": buy_display,
        "SELL": p["sell"],
        "USDC": p["usdc"],
        "Profit Bot": round(profit,4)
    })

df = pd.DataFrame(table)

st.subheader("📊 Bots actifs")
st.dataframe(df, use_container_width=True)

# -------------------------
# Profit total
# -------------------------

st.subheader("💰 Profit total")
st.success(round(profit_total,4))

# -------------------------
# Supprimer bot
# -------------------------

if len(st.session_state.paliers) > 0:

    st.subheader("🗑 Supprimer un bot")

    bot_index = st.number_input(
        "Numéro du bot",
        min_value=1,
        max_value=len(st.session_state.paliers),
        step=1
    )

    if st.button("Supprimer Bot"):
        st.session_state.paliers.pop(bot_index-1)
        st.rerun()

# -------------------------
# Boutons bot
# -------------------------

col1,col2 = st.columns(2)

with col1:
    st.button("▶ Start Bot")

with col2:
    st.button("⏹ Stop Bot")
