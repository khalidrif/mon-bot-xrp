import streamlit as st
import ccxt
import time

st.title("🔄 Bot XRP Automatique : Achat ➡️ Vente")

# Connexion Kraken
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    st.sidebar.success("Connecté à Kraken")
except Exception as e:
    st.sidebar.error(f"Erreur : {e}")
    st.stop()

# Configuration
symbol = 'XRP/USDC'
st.subheader("⚙️ Paramètres du Cycle")

col1, col2, col3 = st.columns(3)
with col1:
    p_achat = st.number_input("Prix d'ACHAT (USDC)", value=2.4000, format="%.4f")
with col2:
    p_vente = st.number_input("Prix de VENTE (USDC)", value=2.5000, format="%.4f")
with col3:
    montant = st.number_input("Montant (XRP)", value=20.0, step=1.0)

# État du bot
if 'running' not in st.session_state:
    st.session_state.running = False

def run_bot():
    status = st.empty()
    logs = st.empty()
    
    while st.session_state.running:
        # ÉTAPE 1 : PLACER L'ACHAT
        status.warning(f"⏳ Placement de l'ordre d'ACHAT à {p_achat}...")
        order_buy = exchange.create_limit_buy_order(symbol, montant, p_achat)
        order_id = order_buy['id']
        
        # Attendre que l'achat soit rempli
        while True:
            check = exchange.fetch_order(order_id, symbol)
            if check['status'] == 'closed':
                status.success(f"✅ ACHAT terminé à {p_achat} !")
                break
            time.sleep(10) # Vérification toutes les 10 secondes
            if not st.session_state.running: return

        # ÉTAPE 2 : PLACER LA VENTE
        status.warning(f"⏳ Placement de l'ordre de VENTE à {p_vente}...")
        order_sell = exchange.create_limit_sell_order(symbol, montant, p_vente)
        order_id = order_sell['id']
        
        # Attendre que la vente soit remplie
        while True:
            check = exchange.fetch_order(order_id, symbol)
            if check['status'] == 'closed':
                status.success(f"💰 VENTE terminée à {p_vente} ! Profit réalisé.")
                break
            time.sleep(10)
            if not st.session_state.running: return
        
        st.toast("Cycle terminé, on recommence !")
        time.sleep(2)

# Boutons de contrôle
if not st.session_state.running:
    if st.button("▶️ DÉMARRER LE BOT"):
        st.session_state.running = True
        run_bot()
else:
    if st.button("⏹️ ARRÊTER LE BOT"):
        st.session_state.running = False
        st.experimental_rerun()
