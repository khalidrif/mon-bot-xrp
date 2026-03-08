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
        st.rerun()

# -------------------------
# Bots actifs
# -------------------------

st.subheader("📊 Bots actifs")

profit_total = 0

for i,p in enumerate(st.session_state.paliers):

    col1,col2,col3,col4,col5,col6 = st.columns(6)

    # couleur BUY
    if p["buy_done"]:
        buy_display = f"🟢 {p['buy']}"
    else:
        buy_display = f"{p['buy']}"

    profit = (p["sell"] - p["buy"]) * (p["usdc"] / p["buy"])
    profit_total += profit

    col1.write(f"Bot {i+1}")
    col2.write(f"BUY : {buy_display}")
    col3.write(f"SELL : 🔴 {p['sell']}")
    col4.write(f"USDC : {p['usdc']}")
    col5.write(f"Profit : {round(profit,4)}")

    # bouton achat
    if col6.button("Acheter", key=f"buy{i}"):
        p["buy_done"] = True
        st.rerun()

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
