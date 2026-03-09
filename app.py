import streamlit as st
import ccxt
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Grid Bot", layout="wide")
st.title("🧱 Bot XRP/USDC - Multi-Fourchettes (Grid)")

# Connexion Kraken
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_API_KEY"],
    'secret': st.secrets["KRAKEN_API_SECRET"],
    'enableRateLimit': True
})

# --- RÉGLAGES DANS LA BARRE LATÉRALE ---
with st.sidebar:
    st.header("📊 Paramètres de la Grille")
    nb_paliers = st.slider("Nombre de paliers d'achat", 1, 5, 3)
    ecart_palier = st.slider("Écart entre paliers (%)", 0.5, 5.0, 1.0) / 100
    mise_par_palier = st.number_input("Mise par palier (USDC)", value=15.0)
    profit_target = st.slider("Objectif Profit par palier (%)", 0.5, 5.0, 1.5) / 100

# --- ÉTAT DU BOT ---
if 'last_price' not in st.session_state:
    st.session_state.last_price = 0.0
if 'actif' not in st.session_state:
    st.session_state.actif = False

# --- INTERFACE ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LA GRILLE", type="primary", use_container_width=True):
    st.session_state.actif = True
if c2.button("🛑 ARRÊTER", use_container_width=True):
    st.session_state.actif = False

st.divider()

if st.session_state.actif:
    try:
        ticker = exchange.fetch_ticker('XRP/USDC')
        current_price = ticker['last']
        
        if st.session_state.last_price == 0.0:
            st.session_state.last_price = current_price

        # --- AFFICHAGE DES FOURCHETTES ---
        st.subheader("🎯 Vos Fourchettes Actuelles")
        cols = st.columns(nb_paliers)
        
        for i in range(1, nb_paliers + 1):
            prix_achat = st.session_state.last_price * (1 - (ecart_palier * i))
            prix_vente = st.session_state.last_price * (1 + (profit_target * i))
            
            with cols[i-1]:
                st.metric(f"Palier {i}", f"{prix_achat:.4f}", f"-{ecart_palier*i*100:.1%}", delta_color="inverse")
                st.caption(f"Vente cible: {prix_vente:.4f}")

        # --- LOGIQUE D'EXÉCUTION (Exemple Palier 1) ---
        diff = (current_price - st.session_state.last_price) / st.session_state.last_price
        
        # Si baisse touche le palier 1
        if diff <= -ecart_palier:
            st.warning(f"⚡ Palier 1 atteint ! Achat de {mise_par_palier} USDC")
            # exchange.create_market_buy_order('XRP/USDC', mise_par_palier / current_price)
            st.session_state.last_price = current_price # On décale la grille vers le bas
            
        # Si hausse touche le profit target
        elif diff >= profit_target:
            st.success(f"💰 Profit Palier 1 atteint ! Vente en cours")
            # exchange.create_market_sell_order('XRP/USDC', xrp_balance)
            st.session_state.last_price = current_price # On décale la grille vers le haut

        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur : {e}")
        time.sleep(10)
        st.rerun()
