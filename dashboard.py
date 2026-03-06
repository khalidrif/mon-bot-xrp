import streamlit as st
import krakenex

# 1. CONNEXION
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

st.title("🤖 BOT XRP GRID")

# 2. RÉGLAGES
c1, c2, c3 = st.columns(3)
p_bas = c1.number_input("Prix Min", value=1.00, format="%.4f")
p_haut = c2.number_input("Prix Max", value=1.20, format="%.4f")
n_niveaux = c3.number_input("Niveaux", value=5, min_value=2)
vol = st.number_input("XRP par niveau", value=10.0)

# 3. ACTION : LANCER LA GRILLE
if st.button("🚀 DÉPLOYER LA GRILLE", use_container_width=True):
    intervalle = (p_haut - p_bas) / (n_niveaux - 1)
    
    for i in range(n_niveaux):
        prix_achat = round(p_bas + (i * intervalle), 4)
        prix_vente = round(prix_achat + intervalle, 4)
        
        # Ordre Achat qui déclenche une Vente dès qu'il est rempli
        params = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
            'price': str(prix_achat), 'volume': str(vol),
            'close[ordertype]': 'limit', 'close[price]': str(prix_vente), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', params)
    st.success("Grille placée sur Kraken !")

st.divider()

# 4. MONITORING & STOP
try:
    ordres = k.query_private('OpenOrders')['result']['open']
    if ordres:
        st.write(f"📈 {len(ordres)} ordres actifs")
        if st.button("🗑️ TOUT ANNULER", type="primary"):
            k.query_private('CancelAll')
            st.rerun()
    else:
        st.info("Aucun bot en cours.")
except:
    st.error("Vérifie tes clés API.")
