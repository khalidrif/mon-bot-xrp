import streamlit as st
import ccxt  # <--- Vérifie bien que cette ligne est présente
import time

st.title("Bot XRP/USDC Kraken")

# 1. INITIALISATION DE L'API
# On place l'initialisation dans un bloc try pour éviter le crash au démarrage
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    st.success("Connexion API configurée !")
except Exception as e:
    st.error(f"Erreur de configuration : {e}")
    st.stop() # Arrête l'exécution si les clés manquent

# 2. PARAMÈTRES
SYMBOL = 'XRP/USDC'
quantite = st.number_input("Quantité XRP", value=30)

if st.button("Lancer le Bot"):
    status = st.empty()
    prix_tick = st.empty()
    
    while True:
        try:
            ticker = exchange.fetch_ticker(SYMBOL)
            prix = ticker['last']
            prix_tick.metric("Prix Actuel", f"{prix} USDC")
            
            # Logique d'achat/vente ici...
            status.info("Bot en recherche d'opportunité...")
            
        except Exception as e:
            st.error(f"Erreur pendant le cycle : {e}")
            break
        
        time.sleep(20)
