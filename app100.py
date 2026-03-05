import streamlit as st
import ccxt
import time
from config import get_kraken_connection

# 1. STYLE CLAIR ET NET
st.set_page_config(page_title="XRP 100 BOTS", layout="wide")
st.markdown("""
    <style>
    .bot-row { border-bottom: 1px solid #ddd; padding: 5px; display: flex; justify-content: space-between; font-family: monospace; }
    .status-idle { color: #ccc; }
    .status-active { color: #007bff; font-weight: bold; }
    .badge-cash { background-color: #FFD700; color: black; padding: 2px 5px; font-weight: bold; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)

# 2. INITIALISATION MÉMOIRE (NOM UNIQUE POUR FORCER)
if 'session_100_bots' not in st.session_state:
    st.session_state.session_100_bots = {f"B{i+1}": {"status": "IDLE", "pa": 0.0, "pv": 0.0} for i in range(100)}

# --- SIDEBAR ULTRA-LÉGÈRE (UN SEUL BOUTON) ---
with st.sidebar:
    st.header("⚡ COMMANDES")
    bot_selectionne = st.selectbox("CHOISIR UN BOT", [f"B{i+1}" for i in range(100)])
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    
    if st.button(f"🚀 LANCER {bot_selectionne}"):
        st.session_state.session_100_bots[bot_selectionne].update({"status": "ACHAT", "pa": p_in, "pv": p_out})
        st.success(f"{bot_selectionne} est maintenant ACTIF")

    if st.button("🚨 RESET TOTAL"):
        st.session_state.session_100_bots = {f"B{i+1}": {"status": "IDLE", "pa": 0.0, "pv": 0.0} for i in range(100)}
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title("🖥️ TERMINAL XRP - 100 BOTS")

# AFFICHAGE STRICT DES 100 LIGNES
for i in range(100):
    name = f"B{i+1}"
    bot = st.session_state.session_100_bots[name]
    st_class = "status-active" if bot["status"] != "IDLE" else "status-idle"
    
    st.markdown(f'''
        <div class="bot-row">
            <span style="font-weight:bold; width:50px;">{name}</span>
            <span class="{st_class}">{bot["status"]}</span>
            <span>{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
            <span class="badge-cash">25.00 $</span>
        </div>
    ''', unsafe_allow_html=True)
