import streamlit as st
import krakenex

st.title("🤖 Test de Connexion Kraken")

# Test direct des secrets
if "KRAKEN_KEY" not in st.secrets:
    st.error("❌ Les Secrets ne sont pas configurés dans Streamlit Settings !")
else:
    try:
        k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])
        res = k.query_public('Ticker', {'pair': 'XRPUSDC'})
        prix = res['result']['XRPUSDC']['c'][0]
        
        st.success(f"✅ Connexion réussie ! Prix XRP : {prix} USDC")
        
        # Affichage du solde brut pour tester
        bal = k.query_private('Balance')['result']
        st.write("### Solde Brut :")
        st.json(bal)
        
    except Exception as e:
        st.error(f"❌ Erreur Kraken : {e}")
