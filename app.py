import streamlit as st
import ccxt
import time

# Initialisation
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_KEY"],
    'secret': st.secrets["KRAKEN_SECRET"],
    'enableRateLimit': True,
    'options': {'nonce': lambda: int(time.time() * 1000)}
})

st.title("Test Envoi Ordre Kraken")

if st.button("🚀 TESTER ACHAT IMMEDIAT"):
    try:
        # 1. Vérification du solde avant l'ordre
        bal = exchange.fetch_balance()
        usdc = bal.get('USDC', {}).get('free', 0)
        st.write(f"Solde USDC : {usdc}")

        # 2. Tentative d'achat (Montant minimum 20 XRP pour éviter l'erreur de taille)
        st.write("Envoi de l'ordre XRP/USDC...")
        order = exchange.create_market_buy_order('XRP/USDC', 20)
        
        st.success("✅ ORDRE ENVOYÉ AVEC SUCCÈS !")
        st.json(order)
        
    except Exception as e:
        # C'EST ICI QUE TU VERRAS LA VRAIE ERREUR
        st.error(f"❌ L'ORDRE A ÉCHOUÉ : {e}")
