import streamlit as st
import krakenex
import os
import pandas as pd

# Titre
st.title("📈 Mon Bot XRP")

try:
    # Connexion
    k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])
    
    # Récupérer le prix
    res = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix = float(res['result']['XRPUSDC']['c'][0])
    
    # Affichage simple
    st.metric("Prix XRP actuel", f"{prix} USDC")
    
    # Récupérer le solde
    bal = k.query_private('Balance')['result']
    st.write("### Mon Portefeuille")
    st.dataframe(pd.DataFrame.from_dict(bal, orient='index', columns=['Quantité']))

except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.info("Vérifiez vos Secrets dans Streamlit Settings")
