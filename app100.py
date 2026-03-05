import streamlit as st
import json
import os

# 1. STYLE CLAIR (PAS NOIR)
st.set_page_config(page_title="XRP 100 BOTS", layout="wide")
st.markdown("""
    <style>
    .bot-line { 
        border-bottom: 1px solid #eee; 
        padding: 8px; 
        display: flex; 
        justify-content: space-between; 
        font-family: monospace;
    }
    .flash-box { background-color: #ffc107; color: black; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. INITIALISATION FORCÉE À 100
# On ne regarde pas le fichier JSON pour l'instant, on force 100 en mémoire
if 'bots' not in st.session_state or len(st.session_state.bots) < 100:
    st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 1.40, "pv": 1.45, "budget": 25.0} for i in range(100)}

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ CMD")
    if st.button("🚨 RESET TOTAL (FORCE 100)"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 1.40, "pv": 1.45, "budget": 25.0} for i in range(100)}
        st.rerun()

# --- AFFICHAGE DES 100 ---
st.title("🖥️ TERMINAL XRP - 100 BOTS")

# Boucle stricte de 1 à 100
for i in range(100):
    name = f"B{i+1}"
    bot = st.session_state.bots[name]
    st.markdown(f'''
        <div class="bot-line">
            <span style="font-weight:bold; width:50px;">{name}</span>
            <span style="color:#888; width:100px;">{bot["status"]}</span>
            <span>{bot["pa"]} → {bot["pv"]}</span>
            <span class="flash-box">25.00 $</span>
        </div>
    ''', unsafe_allow_html=True)
