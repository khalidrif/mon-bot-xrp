import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Kraken XRP Grid", layout="wide")

# --- CONNEXION ---
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    st.success("✅ Connecté à Kraken")
except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")
    st.stop()

st.title("🤖 XRP Multi-Bot Automatique")

# --- CONFIGURATION DES BOTS ---
st.write("### ⚙️ Paramètres des Bots")

col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
with col1: 
    p1_buy = st.number_input("Bot 1 : Achat", value=2.450, format="%.3f")
    p2_buy = st.number_input("Bot 2 : Achat", value=2.350, format="%.3f")
with col2:
    p1_sell = st.number_input("Bot 1 : Vente", value=2.550, format="%.3f")
    p2_sell = st.number_input("Bot 2 : Vente", value=2.450, format="%.3f")
with col3:
    qty1 = st.number_input("Bot 1 : Quantité", value=20.0, key="q1")
    qty2 = st.number_input("Bot 2 : Quantité", value=20.0, key="q2")
with col4:
    st.write("") # Espace
    run_btn = st.button("▶️ DÉMARRER")
    stop_btn = st.button("⏹️ ARRÊTER")

st.divider()

# --- ZONE DE SUIVI (LOGS) ---
st.write("### 📊 État des Bots en Temps Réel")
status_bot1 = st.empty()
status_bot2 = st.empty()

# Gestion de l'exécution
if run_btn:
    st.session_state.active = True
if stop_btn:
    st.session_state.active = False
    st.warning("Arrêt demandé... Le bot finira sa vérification en cours.")

# --- LOGIQUE DE BOUCLE ---
if st.session_state.get('active'):
    symbol = 'XRP/USDC'
    
    # Initialisation simplifiée pour l'exemple (1 cycle par bot alternativement)
    while st.session_state.active:
        # BOT 1 : Vérification/Action
        status_bot1.info(f"🔄 **Bot 1** : Placement ordre d'achat à **{p1_buy}**...")
        # Ici on place l'ordre et on attend (logique simplifiée)
        # Pour une version "H24", le script attendrait ici l'exécution de Kraken
        
        time.sleep(2) # Simulation de latence réseau
        status_bot1.warning(f"⏳ **Bot 1** : En attente d'exécution sur Kraken...")
        
        # BOT 2 : Vérification/Action
        status_bot2.info(f"🔄 **Bot 2** : Placement ordre d'achat à **{p2_buy}**...")
        
        time.sleep(5) # Pause pour ne pas saturer l'API Kraken
        
        # Note : Dans Streamlit, cette boucle bloque l'interface. 
        # Pour arrêter, il faut souvent rafraîchir la page ou utiliser le bouton Stop.
else:
    st.info("Bots en pause. Cliquez sur Démarrer pour lancer les cycles.")
