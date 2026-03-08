import streamlit as st
import pandas as pd

st.set_page_config(page_title="XRP Bot", layout="wide")

st.title("🤖 XRP Trading Bot")

# -------------------------
# Initialisation bots
# -------------------------

if "paliers" not in st.session_state:
    st.session_state.paliers = [
        {"buy":1.33607,"sell":1.37607,"usdc":10,"buy_done":False},
        {"buy":1.32000,"sell":1.36000,"usdc":10,"buy_done":False},
        {"buy":1.30000,"sell":1.34000,"usdc":10,"buy_done":False},
    ]


# -------------------------
# Style barre montant
# -------------------------

st.markdown("""
<style>

.stNumberInput input{
height:45px;
font-size:18px;
border-radius:10px;
border:1px solid #ddd;
}

.buy{
color:green;
font-weight:bold;
}

.sell{
color:red;
font-weight:bold;
}

</style>
""", unsafe_allow_html=True)


# -------------------------
# Barre montant
# -------------------------

st.subheader("💰 Montant USDC")

montant = st.number_input(
"Montant par bot",
min_value=1.0,
value=10.0,
step=1.0
)

# appliquer montant
for p in st.session_state.paliers:
    p["usdc"] = montant


# -------------------------
# Simulation prix XRP
# -------------------------

prix = st.number_input(
"Prix XRP",
value=1.34,
step=0.001
)

st.write("Prix actuel :", prix)


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

    profit = (p["sell"]-p["buy"]) * (p["usdc"]/p["buy"])
    profit_total += profit

    buy_color = "🟢 "+str(p["buy"]) if p["buy_done"] else str(p["buy"])

    table.append({
        "Bot":i+1,
        "BUY":buy_color,
        "SELL":p["sell"],
        "USDC":p["usdc"],
        "Profit Bot":round(profit,4)
    })


df = pd.DataFrame(table)

st.dataframe(df,use_container_width=True)


# -------------------------
# Profit total
# -------------------------

st.subheader("💵 Profit total")

st.success(round(profit_total,4))


# -------------------------
# Boutons
# -------------------------

col1,col2 = st.columns(2)

with col1:
    if st.button("▶ Start Bot"):
        st.success("Bot activé")

with col2:
    if st.button("⏹ Stop Bot"):
        st.warning("Bot arrêté")
