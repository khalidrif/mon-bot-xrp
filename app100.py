import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. CONFIGURATION ET STYLE BLOOMBERG LIGHT
st.set_page_config(page_title="XRP 100 BOTS TERMINAL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    .css-10trblm { color: #00FF00 !important; } /* Texte vert pour le prix */
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION KRAKEN
kraken = get_kraken_connection()

# 3. INITIALISATION DE LA MÉMOIRE (100 LIGNES)
if 'df_bots' not in st.session_state:
    # On crée un tableau propre de 100 lignes
    data = []
    for i in range(1, 101):
        data.append({
            "BOT": f"B{i}",
            "STATUS": "IDLE",
            "TARGET_IN": 1.4000,
            "TARGET_OUT": 1.4500,
            "BUDGET": 25.0,
            "CYCLES": 0
        })
    st.session_state.df_bots = pd.DataFrame(data)
    st.session_state.net_gain = 0.0

# --- SIDEBAR : LE POSTE DE COMMANDE ---
with st.sidebar:
    st.header("⚡ COMMAND CENTER")
    bot_selectionne = st.selectbox("SÉLECTIONNER BOT", st.session_state.df_bots["BOT"])
    p_in = st.number_input("PRIX ACHAT (IN)", value=1.4000, format="%.4f")
    p_out = st.number_input("PRIX VENTE (OUT)", value=1.4500, format="%.4f")
    budget = st.number_input("BUDGET (USDC)", value=25.0)
    
    if st.button(f"🚀 LANCER {bot_selectionne}"):
        idx = int(bot_selectionne[1:]) - 1
        # Action Kraken réelle
        try:
            if not kraken.markets: kraken.load_markets()
            pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
            vol = float(kraken.amount_to_precision('XRP/USDC', budget / pa_f))
            res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
            
            # Mise à jour du tableau
            st.session_state.df_bots.at[idx, "STATUS"] = "ACHAT"
            st.session_state.df_bots.at[idx, "TARGET_IN"] = p_in
            st.session_state.df_bots.at[idx, "TARGET_OUT"] = p_out
            st.session_state.df_bots.at[idx, "BUDGET"] = budget
            st.success(f"{bot_selectionne} envoyé à Kraken !")
        except Exception as e:
            st.error(f"Erreur Kraken : {str(e)[:50]}")

    if st.button("🚨 RESET TOTAL (FORCE 100)"):
        st.session_state.df_bots = pd.DataFrame([{"BOT": f"B{i+1}", "STATUS": "IDLE", "TARGET_IN": 1.400, "TARGET_OUT": 1.450, "BUDGET": 25.0, "CYCLES": 0} for i in range(100)])
        st.session_state.net_gain = 0.0
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title("🖥️ TERMINAL XRP - 100 BOTS")

# PRIX LIVE
try:
    ticker = kraken.fetch_ticker('XRP/USDC')
    px = ticker['last']
    st.metric("XRP INDEX PRICE", f"{px:.4f} USDC", delta=None)
except:
    px = 1.40
    st.warning("Connexion Kraken...")

st.write(f"**NET GAIN TOTAL : +{st.session_state.net_gain:.4f} USDC**")

# --- LE TABLEAU DES 100 BOTS (SCROLLABLE & ULTRA RAPIDE) ---
# On affiche le dataframe de 100 lignes d'un coup
st.dataframe(
    st.session_state.df_bots.style.applymap(
        lambda x: 'color: orange' if x == 'ACHAT' else ('color: green' if x == 'VENTE' else 'color: gray'), 
        subset=['STATUS']
    ),
    use_container_width=True,
    height=800 # Hauteur fixe pour voir les 100 bots avec un scroll
)

# Rafraîchissement automatique toutes les 15 secondes
time.sleep(15)
st.rerun()
