import streamlit as st
import ccxt
import time
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Grid Bot 50", layout="wide")
st.title("🤖 XRP Grid Bot - 50 Niveaux")

@st.cache_resource
def get_exchange():
    ex = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': 'milliseconds'}
    })
    ex.load_markets()
    return ex

exchange = get_exchange()
symbol = "XRP/USDC"

# --- PARAMÈTRES DE LA GRILLE ---
with st.sidebar:
    st.header("📊 Configuration Grille")
    prix_min = st.number_input("Prix Plancher (Bas)", value=1.2000, format="%.4f")
    prix_max = st.number_input("Prix Plafond (Haut)", value=1.5000, format="%.4f")
    nb_grilles = st.number_input("Nombre de grilles", value=50, min_value=2)
    mise_totale = st.number_input("Investissement Total (USDC)", value=500.0)
    
    st.divider()
    if st.button("🚀 GÉNÉRER LA GRILLE"):
        # Calcul des paliers
        st.session_state.niveaux = np.linspace(prix_min, prix_max, nb_grilles)
        st.session_state.mise_par_palier = mise_totale / nb_grilles
        st.success(f"Grille de {nb_grilles} niveaux prête !")

# --- ÉTAT DU BOT ---
if 'actif' not in st.session_state: st.session_state.actif = False
if 'niveaux' not in st.session_state: st.session_state.niveaux = []

# --- AFFICHAGE ---
ticker = exchange.fetch_ticker(symbol)
prix_actuel = ticker['last']
st.metric("Prix XRP Actuel", f"{prix_actuel:.4f} USDC")

c1, c2 = st.columns(2)
if c1.button("DÉMARRER LA GRILLE", type="primary", use_container_width=True):
    st.session_state.actif = True
if c2.button("STOP", use_container_width=True):
    st.session_state.actif = False

# --- LOGIQUE GRID ---
if st.session_state.actif and len(st.session_state.niveaux) > 0:
    st.info(f"Le bot surveille {len(st.session_state.niveaux)} niveaux entre {prix_min} et {prix_max}")
    
    # On itère sur chaque niveau de la grille
    for niveau in st.session_state.niveaux:
        # Si le prix actuel croise un niveau vers le bas -> ACHAT
        if prix_actuel <= niveau and prix_actuel > niveau * 0.998:
             st.write(f"🎯 Niveau touché : {niveau:.4f} -> Tentative d'ordre...")
             # Ici on placerait un Limit Order (Code simplifié pour l'exemple)
             # qty = mise_par_palier / niveau
             # exchange.create_limit_buy_order(symbol, qty, niveau)
    
    time.sleep(30)
    st.rerun()
else:
    st.warning("Configurez la grille et cliquez sur Démarrer.")
