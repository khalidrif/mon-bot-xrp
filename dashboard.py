import streamlit as st
import krakenex
import time

# --- CONFIGURATION API ---
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

st.set_page_config(page_title="XRP Grid Bot", layout="centered")
st.title("🕸️ XRP Grid Trading Bot")

# --- PARAMÈTRES DE LA GRILLE ---
with st.sidebar:
    st.header("Réglages de la Grille")
    p_min = st.number_input("Prix Bas (Support)", value=1.0000, format="%.4f")
    p_max = st.number_input("Prix Haut (Résistance)", value=1.2000, format="%.4f")
    n_grids = st.number_input("Nombre de Grilles (Niveaux)", value=5, min_value=2)
    vol_per_grid = st.number_input("Volume XRP par niveau", value=10.0)
    
    st.divider()
    if st.button("🔴 STOP & ANNULER TOUT", type="primary", use_container_width=True):
        k.query_private('CancelAll')
        st.cache_data.clear()
        st.rerun()

# --- LOGIQUE DE CALCUL ---
# Génère les niveaux de prix entre min et max
niveaux = [round(p_min + (p_max - p_min) * i / (n_grids - 1), 4) for i in range(n_grids)]

# --- INTERFACE ---
c1, c2 = st.columns(2)

if c1.button("🚀 LANCER LA GRILLE", use_container_width=True):
    # Récupérer le prix actuel pour savoir où placer les achats et les ventes
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(ticker['result']['XRPUSDC']['c'][0])
    
    st.info(f"Prix actuel : {prix_actuel}$. Placement des ordres...")
    
    for p in niveaux:
        # Si le niveau est sous le prix actuel -> ACHAT
        if p < prix_actuel:
            type_o = 'buy'
            p_tp = p * 1.02 # On revend 2% plus haut par défaut
        # Si le niveau est au dessus -> VENTE
        else:
            type_o = 'sell'
            p_tp = p * 0.98 # On rachete 2% plus bas par défaut
            
        params = {
            'pair': 'XRPUSDC',
            'type': type_o,
            'ordertype': 'limit',
            'price': str(p),
            'volume': str(vol_per_grid),
            'close[ordertype]': 'limit',
            'close[price]': str(round(p_tp, 4)),
            'close[type]': 'sell' if type_o == 'buy' else 'buy'
        }
        k.query_private('AddOrder', params)
    st.success(f"Grille de {n_grids} niveaux déployée !")

# --- MONITORING ---
st.subheader("📦 État de ta grille")
try:
    res = k.query_private('OpenOrders').get('result', {}).get('open', {})
    if res:
        st.write(f"Nombre d'ordres actifs : **{len(res)}**")
        for oid, det in res.items():
            st.caption(f"ID: {oid[:5]}.. | {det['descr']['order']}")
    else:
        st.info("Aucune grille active.")
except:
    st.warning("Connexion en attente...")

# Rafraîchissement automatique pour simuler la boucle
time.sleep(10)
st.rerun()
