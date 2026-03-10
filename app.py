import streamlit as st
import ccxt

# TITRE DE TEST (Si tu vois ça, la mise à jour a marché !)
st.title("🚀 TEST DE MISE À JOUR RÉUSSIE")
st.write("Si tu lis ce message, Streamlit utilise bien ton nouveau code.")

# TEST DES SECRETS
try:
    api_key = st.secrets["KRAKEN_API_KEY"]
    st.success("✅ Les Secrets (Clés API) sont bien détectés !")
except Exception as e:
    st.error("❌ Les Secrets ne sont pas configurés correctement dans Streamlit Cloud.")

# TEST DE CONNEXION KRAKEN
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
    })
    ticker = exchange.fetch_ticker('XRP/USDC')
    st.info(f"📈 Connexion Kraken OK ! Prix actuel du XRP : {ticker['last']} USDC")
except Exception as e:
    st.error(f"❌ Erreur de connexion à Kraken : {e}")

st.divider()
st.write("Une fois que ce test affiche 'REUSSIE', tu pourras remettre le code complet du bot.")
