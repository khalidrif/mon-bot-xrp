import streamlit as st
import ccxt
import time

# 1. Connexion ultra-rapide
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_API_KEY"],
    'secret': st.secrets["KRAKEN_API_SECRET"]
})

st.title("⚡ Bot Flash XRP")
cible = 1.30
# 1. Récupération des soldes réels
balance = exchange.fetch_balance()
solde_usdc = balance['free'].get('USDC', 0.0)
solde_xrp = balance['free'].get('XRP', 0.0)

# 2. Affichage visuel (en colonnes)
col1, col2 = st.columns(2)
col1.metric(label="Portefeuille USDC", value=f"{solde_usdc:.2f} $")
col2.metric(label="Stock XRP", value=f"{solde_xrp:.2f} XRP")

# 2. LA MINI BOUCLE
while True:
    try:
        # Lire le prix
        prix = exchange.fetch_ticker('XRP/USDC')['last']
        st.write(f"🔍 Prix : {prix} | Cible : {cible}")

        # Condition d'achat
        if prix <= cible:
            st.success("🚀 ACHAT DÉCLENCHÉ !")
            qty = float(exchange.amount_to_precision('XRP/USDC', 20 / prix))
            exchange.create_market_buy_order('XRP/USDC', qty)
            st.stop() # On arrête tout après l'achat

    except Exception as e:
        st.error(f"Erreur : {e}")

    # Pause courte (10 secondes) et relance
    time.sleep(10)
    st.rerun()
