import streamlit as st
import time
import json
import os

# 1. STYLE BLOOMBERG (STRICT) - PLACÉ TOUT EN HAUT
st.set_page_config(page_title="XRP 100 BOTS", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    .bot-line { 
        border-bottom: 1px dotted #222; 
        padding: 5px; 
        display: flex; 
        justify-content: space-between; 
        color: white;
        font-family: 'Courier New', monospace;
        font-size: 13px;
    }
    .flash-box { background-color: #FFFF00; color: #000; padding: 0 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. INITIALISATION MÉMOIRE (SANS KRAKEN POUR L'INSTANT)
if 'bots' not in st.session_state:
    st.session_state.bots = {f"B{i+1}": {"status": "IDLE", "pa": 1.40, "pv": 1.45, "budget": 25.0} for i in range(100)}

# --- TITRE ---
st.title("📊 TERMINAL XRP - 100 BOTS")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ CONTROLE")
    if st.button("🚨 RESET FORCE 100"):
        st.session_state.bots = {f"B{i+1}": {"status": "IDLE", "pa": 1.40, "pv": 1.45, "budget": 25.0} for i in range(100)}
        st.rerun()

# --- ZONE D'AFFICHAGE (STRICTE) ---
container = st.container()

with container:
    # On affiche les 100 lignes immédiatement
    for i in range(100):
        name = f"B{i+1}"
        bot = st.session_state.bots[name]
        st.markdown(f'''
            <div class="bot-line">
                <span style="color:#555;">{name}</span>
                <span style="color:#444;">{bot["status"]}</span>
                <span>{bot["pa"]} -> {bot["pv"]}</span>
                <span class="flash-box">{bot["budget"]}$</span>
            </div>
        ''', unsafe_allow_html=True)

# 3. TENTATIVE DE CONNEXION KRAKEN (APRES L'AFFICHAGE)
try:
    from config import get_kraken_connection
    kraken = get_kraken_connection()
    if kraken:
        st.success("✅ KRAKEN CONNECTÉ")
except Exception as e:
    st.error(f"❌ ERREUR KRAKEN : {e}")
