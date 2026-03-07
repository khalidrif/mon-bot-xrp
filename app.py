import streamlit as st
import ccxt
import time

st.title("双 XRP Grid Bot : Deux Étages Automatiques")

# Connexion Kraken sécurisée
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_API_KEY"],
    'secret': st.secrets["KRAKEN_SECRET"],
    'enableRateLimit': True,
})

def gerer_cycle(nom, p_achat, p_vente, montant, placeholder):
    """Fonction qui gère un cycle Achat -> Vente complet"""
    symbol = 'XRP/USDC'
    
    # 1. ACHAT
    placeholder.warning(f"[{nom}] Attente ACHAT à {p_achat}...")
    ordre_buy = exchange.create_limit_buy_order(symbol, montant, p_achat)
    
    while True:
        check = exchange.fetch_order(ordre_buy['id'], symbol)
        if check['status'] == 'closed':
            placeholder.success(f"[{nom}] ✅ ACHAT Terminé !")
            break
        time.sleep(10)

    # 2. VENTE
    placeholder.warning(f"[{nom}] Attente VENTE à {p_vente}...")
    ordre_sell = exchange.create_limit_sell_order(symbol, montant, p_vente)
    
    while True:
        check = exchange.fetch_order(ordre_sell['id'], symbol)
        if check['status'] == 'closed':
            placeholder.success(f"[{nom}] 💰 VENTE Terminée ! Cycle bouclé.")
            break
        time.sleep(10)

# --- INTERFACE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 Bot Étage HAUT")
    h_achat = st.number_input("Achat Haut", value=2.50, format="%.3f")
    h_vente = st.number_input("Vente Haut", value=2.60, format="%.3f")

with col2:
    st.subheader("📦 Bot Étage BAS")
    b_achat = st.number_input("Achat Bas", value=2.30, format="%.3f")
    b_vente = st.number_input("Vente Bas", value=2.40, format="%.3f")

montant = st.number_input("Montant XRP par étage", value=20.0)

if st.button("🚀 LANCER LES DEUX BOTS EN BOUCLE"):
    st.info("Les bots tournent... Ne fermez pas cette page.")
    
    p1 = st.empty()
    p2 = st.empty()
    
    # Pour Streamlit, on simule le parallélisme avec une vérification alternée
    while True:
        # Note : Pour un vrai multitâche H24, un script simple .py est mieux que Streamlit
        st.write("Vérification des paliers en cours...")
        # Ici on lance la logique simplifiée (un cycle après l'autre ou en simultané via threading)
        # Pour rester simple, ce script gérera le premier palier puis le second
        gerer_cycle("HAUT", h_achat, h_vente, montant, p1)
        gerer_cycle("BAS", b_achat, b_vente, montant, p2)
