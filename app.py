import streamlit as st
import ccxt

st.title("Test Connexion Kraken 🐙")

# 1. Vérification de la présence des clés
if "KRAKEN_API_KEY" not in st.secrets or "KRAKEN_SECRET" not in st.secrets:
    st.error("⚠️ Clés manquantes dans les Secrets Streamlit !")
    st.info("Vérifiez que vous avez bien ajouté KRAKEN_API_KEY et KRAKEN_SECRET.")
    st.stop()

# 2. Tentative de connexion
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })

    # 3. Appel de l'API privée (Demander le solde)
    balance = exchange.fetch_balance()
    
    st.success("✅ Connexion réussie !")
    st.subheader("Vos soldes disponibles :")
    
    # Afficher uniquement les cryptos dont le solde est > 0
    for coin, amount in balance['total'].items():
        if amount > 0:
            st.write(f"**{coin}**: {amount}")

except Exception as e:
    st.error(f"❌ Échec de la connexion : {e}")
    st.warning("Vérifiez vos permissions API sur Kraken (Query Funds doit être coché).")
