import streamlit as st
import krakenex

# 1. CONNEXION (Utilise tes secrets GitHub/Streamlit)
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

st.title("🤖 XRP BASE BOT")

# 2. FONCTIONS CŒUR (ACHETER / VENDRE)
def placer_ordre(type_ordre, prix, volume):
    params = {
        'pair': 'XRPUSDC',
        'type': type_ordre,         # 'buy' ou 'sell'
        'ordertype': 'limit',
        'price': str(round(prix, 4)),
        'volume': str(volume)
    }
    return k.query_private('AddOrder', params)

# 3. INTERFACE DE COMMANDE
col1, col2 = st.columns(2)

with col1:
    st.subheader("Entrée")
    prix_achat = st.number_input("Prix Achat", value=1.0000, format="%.4f")
    vol_achat = st.number_input("Quantité", value=10.0, key="buy_vol")
    if st.button("PLACER ACHAT"):
        res = placer_ordre('buy', prix_achat, vol_achat)
        st.write(res)

with col2:
    st.subheader("Sortie")
    prix_vente = st.number_input("Prix Vente", value=1.1000, format="%.4f")
    vol_vente = st.number_input("Quantité", value=10.0, key="sell_vol")
    if st.button("PLACER VENTE"):
        res = placer_ordre('sell', prix_vente, vol_vente)
        st.write(res)

# 4. LISTE DES ORDRES ACTIFS
st.divider()
st.subheader("Ordres Ouverts")
try:
    ordres = k.query_private('OpenOrders')['result']['open']
    if ordres:
        for oid, details in ordres.items():
            st.write(f"ID: {oid} | {details['descr']['order']}")
            if st.button("Annuler", key=oid):
                k.query_private('CancelOrder', {'txid': oid})
                st.rerun()
    else:
        st.info("Aucun ordre en attente.")
except:
    st.warning("Aucune donnée disponible.")
