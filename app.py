import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.title("Bot Trading XRP")

# Paramètres d'entrée
montant = st.number_input("Montant par palier ($)", value=10)
nb_paliers = st.number_input("Nombre de paliers", value=5)

st.write("---")

# Génération des paliers
paliers = []
prix_depart = 1.33607

for i in range(int(nb_paliers)):
    buy = round(prix_depart - (i * 0.005), 5)
    sell = round(buy + 0.04, 5)

    paliers.append({
        "buy": buy,
        "sell": sell,
        "usdc": montant,
        "gain": 0
    })

# Affichage des barres
for i, p in enumerate(paliers):

    components.html(f"""
    <div style="
    background:#101010;
    width:95%;
    height:32px;
    margin:auto;
    margin-top:6px;
    border-radius:5px;
    font-family:Arial;
    font-size:12px;
    color:white;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding-left:8px;
    padding-right:8px;
    ">

    <span>P{i+1}</span>

    <span style="color:#00ff88;">
    BUY:{p['buy']}
    </span>

    <span style="color:#ff4d4d;">
    SELL:{p['sell']}
    </span>

    <span>${p['usdc']}</span>

    <span>WAIT</span>

    <span>+{p['gain']}</span>

    <button style="
    height:20px;
    font-size:10px;
    background:#cc0000;
    color:white;
    border:none;
    border-radius:3px;">
    OFF
    </button>

    <button style="
    height:20px;
    font-size:10px;
    background:#660000;
    color:white;
    border:none;
    border-radius:3px;">
    DEL
    </button>

    </div>
    """, height=36)
