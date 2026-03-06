import streamlit as st
import krakenex
import pandas as pd

st.title("📈 Dashboard Kraken XRP")

# Connexion via les Secrets Streamlit
try:
    k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])
    
    # 1. Récupérer le prix actuel
    res = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix = float(res['result']['XRPUSDC']['c'][0])
    st.metric("Prix XRP actuel", f"{prix} USDC")

    # 2. Récupérer le solde
    bal = k.query_private('Balance')['result']
    st.write("### Mon Portefeuille")
    # On nettoie les noms (XXRP -> XRP)
    clean_bal = {k.replace('X', '').replace('Z', ''): v for k, v in bal.items() if float(v) > 0}
    st.table(pd.DataFrame.from_dict(clean_bal, orient='index', columns=['Quantité']))

    # 3. Voir les ordres de vente ouverts
    orders = k.query_private('OpenOrders')['result']['open']
    if orders:
        st.write("### 🎯 Ordres de vente en attente")
        for oid, details in orders.items():
            st.info(f"Vente de {details['vol']} XRP à {details['descr']['price']} USDC")
    else:
        st.success("Aucun ordre ouvert : le bot a fini son cycle !")

except Exception as e:
    st.error(f"Erreur : {e}")
