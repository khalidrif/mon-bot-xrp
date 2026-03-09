import streamlit as st
import ccxt
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="XRP Custom Bot", layout="wide")

# --- BARRE LATÉRALE : SAISIE DES PARAMÈTRES ---
with st.sidebar:
    st.header("🔑 Configuration API")
    # Utilisation du type "password" pour masquer les clés à l'écran
    api_key = st.text_input("Kraken API Key", type="password")
    api_secret = st.text_input("Kraken API Secret", type="password")
    
    st.header("⚙️ Paramètres de Stratégie")
    symbol = st.text_input("Paire de trading", value="XRP/USDC")
    stake_amount = st.number_input("Mise initiale (USDC)", min_value=10.0, value=20.0, step=5.0)
    multiplier = st.number_input("Multiplicateur (Boule de neige)", min_value=1.0, value=1.5, step=0.1)
    
    st.header("📈 Seuils d'Exécution")
    profit_target = st.slider("Objectif de profit (%)", 0.5, 10.0, 3.0) / 100
    dip_threshold = st.slider("Rachat si baisse de (%)", 0.5, 10.0, 2.0) / 100

# --- ÉTAT DU BOT ---
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False

# --- LOGIQUE PRINCIPALE ---
st.title("🤖 Tableau de Bord Bot XRP")

col_start, col_stop = st.columns(2)
if col_start.button("🚀 DÉMARRER", use_container_width=True, type="primary"):
    if not api_key or not api_secret:
        st.error("Veuillez saisir vos clés API dans la barre latérale.")
    else:
        st.session_state.bot_running = True

if col_stop.button("🛑 ARRÊTER", use_container_width=True):
    st.session_state.bot_running = False

st.divider()

# --- CONNEXION ET AFFICHAGE ---
if st.session_state.bot_running:
    try:
        # Initialisation avec les saisies utilisateur
        exchange = ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
        
        # Récupération des données en direct
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        
        # Affichage des indicateurs
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Prix {symbol}", f"{price} USDC")
        c2.metric("Solde XRP", f"{bal['free'].get('XRP', 0):.2f}")
        c3.metric("Solde USDC", f"{bal['free'].get('USDC', 0):.2f}")
        
        st.info(f"Analyse en cours... Cible de vente : {price * (1 + profit_target):.4f}")
        
        # Relance automatique toutes les 30 secondes
        time.sleep(30)
        st.rerun()
        
    except Exception as e:
        st.error(f"Erreur : {e}")
        st.session_state.bot_running = False
else:
    st.write("Le bot est actuellement en attente. Configurez vos paramètres à gauche et cliquez sur DÉMARRER.")
