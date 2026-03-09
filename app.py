import streamlit as st
import ccxt
import os
import time

# 1. CONFIGURATION
st.set_page_config(page_title="XRP Bot Control", layout="centered")
st.title("🤖 Contrôle du Bot XRP/USDC")

# Initialisation de l'état (mémoire du bot)
if 'actif' not in st.session_state:
    st.session_state.actif = False

# 2. CONNEXION KRAKEN (Secrets Streamlit)
API_KEY = st.secrets.get("KRAKEN_API_KEY")
API_SECRET = st.secrets.get("KRAKEN_API_SECRET")

try:
    exchange = ccxt.kraken({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True
    })
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# 3. INTERFACE DE COMMANDE
col1, col2 = st.columns(2)

if col1.button("🚀 DÉMARRER", use_container_width=True, type="primary"):
    st.session_state.actif = True

if col2.button("🛑 ARRÊTER", use_container_width=True, type="secondary"):
    st.session_state.actif = False

st.divider()

# 4. ZONE D'AFFICHAGE DYNAMIQUE
status_placeholder = st.empty()
metrics_placeholder = st.container()

# 5. LOGIQUE DE SURVEILLANCE
if st.session_state.actif:
    status_placeholder.success("✅ LE BOT EST EN COURS DE SURVEILLANCE...")
    
    try:
        # Récupération des données
        ticker = exchange.fetch_ticker('XRP/USDC')
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp = bal['free'].get('XRP', 0)
        usdc = bal['free'].get('USDC', 0)

        # Affichage des compteurs
        with metrics_placeholder:
            c1, c2, c3 = st.columns(3)
            c1.metric("Prix XRP", f"{price} USDC")
            c2.metric("Solde XRP", f"{xrp:.2f}")
            c3.metric("Solde USDC", f"{usdc:.2f}")

        # LOGIQUE D'ACHAT/VENTE ICI
        # ex: if price < seuil: exchange.create_market_buy_order(...)

        # PAUSE ET RELANCE AUTOMATIQUE
        st.write(f"Dernière vérification : {time.strftime('%H:%M:%S')}")
        time.sleep(30) # Attend 30 secondes
        st.rerun()    # Relance le script pour mettre à jour l'interface

    except Exception as e:
        st.error(f"Erreur pendant le cycle : {e}")
        time.sleep(10)
        st.rerun()

else:
    status_placeholder.error("❌ LE BOT EST À L'ARRÊT.")
    st.info("Cliquez sur DÉMARRER pour lancer la surveillance du XRP.")
