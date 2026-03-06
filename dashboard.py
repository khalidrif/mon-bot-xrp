import streamlit as st
import krakenex

# 1. CONFIGURATION & CONNEXION
st.set_page_config(page_title="XRP Grid Bot", layout="wide")
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

st.title("🤖 XRP GRID BOT (BITGET STYLE)")

# 2. RÉCUPÉRATION SOLDE & PRIX
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})['result']['XRPUSDC']
    prix_actuel = float(ticker['c'][0])
    
    bal = k.query_private('Balance')['result']
    usdc_dispo = float(bal.get('USDC', 0))
    xrp_dispo = float(bal.get('XRP', 0))
    
    st.sidebar.metric("Prix XRP", f"{prix_actuel:.4f} $")
    st.sidebar.write(f"💰 **Solde :** {usdc_dispo:.2f} USDC | {xrp_dispo:.2f} XRP")
except:
    st.error("Erreur de connexion API. Vérifiez vos secrets.")
    prix_actuel = 1.0

# 3. RÉGLAGES DE LA GRILLE
st.subheader("🚀 Paramètres du Bot")
c1, c2, c3, c4 = st.columns(4)

p_min = c1.number_input("Prix Bas (Support)", value=round(prix_actuel * 0.95, 4), format="%.4f")
p_max = c2.number_input("Prix Haut (Résistance)", value=round(prix_actuel * 1.05, 4), format="%.4f")
n_grids = c3.number_input("Niveaux de grille", value=5, min_value=2)
vol = c4.number_input("XRP par niveau", value=10.0)

# 4. ACTION : DÉPLOIEMENT
if st.button("▶️ DÉMARRER LA GRILLE", use_container_width=True, type="primary"):
    intervalle = (p_max - p_min) / (n_grids - 1)
    
    for i in range(n_grids):
        p_achat = round(p_min + (i * intervalle), 4)
        p_vente = round(p_achat + intervalle, 4)
        
        # Ordre conditionnel : l'achat déclenche la vente sur Kraken
        params = {
            'pair': 'XRPUSDC',
            'type': 'buy',
            'ordertype': 'limit',
            'price': str(p_achat),
            'volume': str(vol),
            'close[ordertype]': 'limit',
            'close[price]': str(p_vente),
            'close[type]': 'sell'
        }
        k.query_private('AddOrder', params)
    
    st.success(f"Grille de {n_grids} niveaux activée !")
    st.rerun()

st.divider()

# 5. GESTION DES ORDRES ACTIFS
st.subheader("📦 Missions en cours")
try:
    ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})
    if ordres:
        for oid, det in ordres.items():
            st.write(f"📍 {det['descr']['order']} | ID: `{oid[:8]}`")
        
        if st.button("🗑️ TOUT ANNULER & STOP", type="secondary"):
            k.query_private('CancelAll')
            st.rerun()
    else:
        st.info("Aucun bot actif pour le moment.")
except:
    pass
