import streamlit as st
import ccxt
import time
from datetime import datetime

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="XRP Monitor", page_icon="📊")
st.title("📊 Tableau de Bord XRP/USDC")

# 2. CONNEXION KRAKEN (Lecture seule)
# Utilise tes Secrets Streamlit pour la sécurité
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
    })
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# 3. ZONE DE RAFRAÎCHISSEMENT
placeholder = st.empty()

while True:
    with placeholder.container():
        try:
            # --- RÉCUPÉRATION DES DONNÉES ---
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_actuel = ticker['last']
            
            balance = exchange.fetch_balance()
            solde_usdc = balance['free'].get('USDC', 0.0)
            solde_xrp = balance['free'].get('XRP', 0.0)
            
            # --- AFFICHAGE VISUEL ---
            st.subheader("💰 Mon Portefeuille")
            col1, col2 = st.columns(2)
            col1.metric("Solde USDC", f"{solde_usdc:.2f} $")
            col2.metric("Stock XRP", f"{solde_xrp:.2f} XRP")
            
            st.divider()
            
            st.subheader("📈 Marché en Direct")
            st.metric("Prix XRP", f"{prix_actuel:.4f} USDC")
            
            # Heure de mise à jour
            st.caption(f"Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            st.error(f"Erreur lors de la lecture : {e}")

    # --- PAUSE ET RELANCE ---
    time.sleep(20) # Attend 20 secondes
    st.rerun()    # Rafraîchit la page pour mettre les chiffres à jour
