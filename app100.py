import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE BLOOMBERG (STRICT)
st.set_page_config(page_title="XRP 100 BOTS", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000 !important; color: #FFFFFF; font-family: 'Courier New', monospace; }
    .stApp { background-color: #000000 !important; }
    .bot-line { border-bottom: 1px solid #222; padding: 4px; display: flex; justify-content: space-between; font-size: 12px; }
    .flash-box { background-color: #FFFF00; color: #000; padding: 0 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION
kraken = get_kraken_connection()

# 3. INITIALISATION
if 'bots' not in st.session_state:
    st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE"} for i in range(100)}
    st.session_state.profit_total = 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ CMD")
    p_in = st.number_input("IN", value=1.4000, format="%.4f")
    p_out = st.number_input("OUT", value=1.4500, format="%.4f")
    if st.button("GO B1"):
        st.session_state.bots["B1"].update({"status": "ACHAT", "pa": p_in, "pv": p_out})
    if st.button("🚨 RESET ALL"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE"} for i in range(100)}
        st.rerun()

# --- AFFICHAGE FIXE (SANS BOUCLE WHILE POUR TESTER) ---
st.write(f"### XRP MARKET FEED")

# Conteneur pour rafraîchir uniquement cette partie
placeholder = st.empty()

# Pour le test, on affiche une fois. Si ça marche, on remettra le rafraîchissement.
with placeholder.container():
    for i in range(100):
        name = f"B{i+1}"
        bot = st.session_state.bots[name]
        st.markdown(f'''
            <div class="bot-line">
                <span>{name}</span>
                <span style="color:#555;">{bot["status"]}</span>
                <span>{bot["pa"]} -> {bot["pv"]}</span>
                <span class="flash-box">{bot["budget"]}$</span>
            </div>
        ''', unsafe_allow_html=True)

# Bouton pour forcer la mise à jour manuelle si besoin
if st.button("🔄 REFRESH"):
    st.rerun()
