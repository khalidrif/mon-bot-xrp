import streamlit as st
import pandas as pd
import time

# 1. CONFIGURATION SIMPLE
st.set_page_config(page_title="XRP 100 BOTS", layout="wide")

# 2. TITRE
st.title("🖥️ TERMINAL XRP - 100 BOTS")

# 3. INITIALISATION FORCEE D'UNE LISTE DE 100
if 'ma_liste_bots' not in st.session_state:
    # Création d'un tableau de 100 lignes
    data = []
    for i in range(1, 101):
        data.append({"BOT": f"B{i}", "STATUT": "IDLE", "ACHAT": 1.40, "VENTE": 1.45, "BUDGET": "25.00$"})
    st.session_state.ma_liste_bots = data

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ CONTROLE")
    if st.button("🚨 RÉINITIALISER TOUT (FORCE 100)"):
        data = []
        for i in range(1, 101):
            data.append({"BOT": f"B{i}", "STATUT": "IDLE", "ACHAT": 1.40, "VENTE": 1.45, "BUDGET": "25.00$"})
        st.session_state.ma_liste_bots = data
        st.rerun()

# --- AFFICHAGE SOUS FORME DE TABLEAU (IMPOSSIBLE A CACHER) ---
df = pd.DataFrame(st.session_state.ma_liste_bots)
st.table(df) # st.table affiche TOUTES les lignes d'un coup sans scroll interne

# RAFRAICHISSEMENT
time.sleep(10)
st.rerun()
