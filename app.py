import streamlit as st
import ccxt

st.title("🛠 Test Connexion Kraken")

# ÉTAPE 1 : Test de l'API
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
    })
    
    # Test de lecture simple
    ticker = exchange.fetch_ticker('XRP/USDC')
    prix = ticker['last']
    st.success(f"✅ Connexion réussie ! Prix XRP : {prix} USDC")
    
    # ÉTAPE 2 : Test du solde
    bal = exchange.fetch_balance()
    usdc = bal['free'].get('USDC', 0.0)
    st.write(f"Ton solde Kraken : **{usdc} USDC**")

except Exception as e:
    st.error(f"❌ ERREUR CRITIQUE : {e}")

# ÉTAPE 3 : Bouton d'action direct
st.divider()
if st.button("Tenter un achat de 15 USDC"):
    try:
        # On calcule la quantité pour 15$ au prix actuel
        prix_achat = ticker['last'] * 0.98 # On vise 2% plus bas
        qty = 15 / prix_achat
        
        st.write(f"Envoi de l'ordre : {qty:.2f} XRP à {prix_achat:.4f}...")
        
        ordre = exchange.create_limit_buy_order('XRP/USDC', qty, prix_achat)
        st.balloons()
        st.success(f"ORDRE PLACÉ ! ID : {ordre['id']}")
    except Exception as e:
        st.error(f"L'achat a échoué : {e}")
