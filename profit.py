import streamlit as st
import ccxt
import time
from datetime import datetime

# 1. CONFIGURATION (Toujours en premier)
st.set_page_config(page_title="Lecture XRP Live")
st.title("📊 Lecture en direct XRP/USDC")

# 2. CONNEXION (Secrets Streamlit)
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
    })
except:
    st.error("Erreur de connexion : Vérifie tes Secrets !")
    st.stop()

# 3. ZONE D'AFFICHAGE (Pour éviter la page blanche)
placeholder = st.empty()

# 4. LA BOUCLE
while True:
    with placeholder.container():
        try:
            # Lire le prix
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix = ticker['last']
            
            # Lire le solde
            balance = exchange.fetch_balance()
            usdc = balance['free'].get('USDC', 0.0)
            xrp = balance['free'].get('XRP', 0.0)
            
            # AFFICHAGE SUR L'ÉCRAN
            st.metric("Prix XRP actuel", f"{prix} USDC")
            
            col1, col2 = st.columns(2)
            col1.write(f"💰 **Solde USDC :** {usdc:.2f}")
            col2.write(f"🪙 **Stock XRP :** {xrp:.2f}")
            
            st.caption(f"Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            st.error(f"Erreur : {e}")
            
    # PAUSE ET RELANCE
    time.sleep(10)
    st.rerun()
