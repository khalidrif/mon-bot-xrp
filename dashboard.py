import streamlit as st
import krakenex

# 1. Connexion (Récupère tes clés dans Secrets GitHub/Streamlit)
k = krakenex.API(key = st.secrets["KRAKEN_KEY"], secret = st.secrets["KRAKEN_SECRET"])

st.title("⚡ XRP Simple Trader")

# 2. Paramètres du Bot
with st.container():
    col1, col2, col3 = st.columns(3)
    p_achat = col1.number_input("Prix d'Achat (USDC)", value=1.0500, format="%.4f")
    p_vente = col2.number_input("Prix de Vente (USDC)", value=1.1000, format="%.4f")
    quantite = col3.number_input("Quantité (XRP)", value=20.0)

# 3. Bouton d'action
if st.button("🚀 LANCER LE CYCLE (ACHAT -> VENTE)", use_container_width=True):
    # On prépare l'ordre d'achat avec une condition de fermeture (vente) intégrée
    params = {
        'pair': 'XRPUSDC',
        'type': 'buy',
        'ordertype': 'limit',
        'price': str(round(p_achat, 4)),
        'volume': str(quantite),
        # Dès que l'achat est complété, Kraken place cet ordre de vente :
        'close[ordertype]': 'limit',
        'close[price]': str(round(p_vente, 4)),
        'close[type]': 'sell'
    }
    
    reponse = k.query_private('AddOrder', params)
    
    if reponse.get('error'):
        st.error(f"Erreur : {reponse['error']}")
    else:
        st.success(f"Bot activé ! ID: {reponse['result']['txid'][0]}")
        st.balloons()

st.divider()

# 4. Affichage des ordres en attente
st.subheader("🤖 Ordres Actifs sur Kraken")
try:
    ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})
    if ordres:
        for oid, info in ordres.items():
            st.code(f"{info['descr']['order']} | ID: {oid}")
            if st.button("❌ Annuler", key=oid):
                k.query_private('CancelOrder', {'txid': oid})
                st.rerun()
    else:
        st.info("Aucun bot ne tourne actuellement.")
except:
    st.warning("Impossible de lire les ordres. Vérifie tes clés API.")
