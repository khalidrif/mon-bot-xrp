import streamlit as st
import ccxt
import time

st.set_page_config(page_title="XRP Profit Bot", layout="centered")
st.title("🤖 XRP Boule de Neige")

# --- CONFIGURATION ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    buy_p = st.number_input("Prix d'Achat (USD)", value=2.50, format="%.4f")
    sell_p = st.number_input("Prix de Vente (USD)", value=2.60, format="%.4f")
    initial_amount = st.number_input("Montant Départ (XRP)", value=20.00)

# Connexion Kraken
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_API_KEY"],
    'secret': st.secrets["KRAKEN_SECRET"],
    'enableRateLimit': True,
})

# États de session
if 'current_xrp' not in st.session_state:
    st.session_state.current_xrp = initial_amount
if 'total_gain_usd' not in st.session_state:
    st.session_state.total_gain_usd = 0.0

# --- AFFICHAGE PRINCIPAL ---
c1, c2 = st.columns(2)

with col1:
    st.metric("Capital Actuel", f"{st.session_state.current_xrp:.2f} XRP")

with col2:
    # Affiche le profit net accumulé en USD
    st.metric("Gain Net Accumulé", f"+{st.session_state.total_gain_usd:.2f} USD", delta="Net (frais inclus)")

status = st.empty()

# --- LOGIQUE DU BOT ---
if st.button("Démarrer le Cycle"):
    st.toast("Bot lancé !")
    
    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USD')
            prix_actuel = ticker['last']
            status.info(f"🔍 Prix : {prix_actuel}$ | Cible Achat : {buy_p}$")

            # 1. PHASE ACHAT
            if prix_actuel <= buy_p:
                status.warning("🛒 Achat déclenché...")
                # exchange.create_limit_buy_order('XRP/USD', st.session_state.current_xrp, buy_p)
                
                # 2. PHASE VENTE
                status.warning("⏳ Attente du prix de vente...")
                while True:
                    p = exchange.fetch_ticker('XRP/USD')['last']
                    if p >= sell_p:
                        # exchange.create_limit_sell_order('XRP/USD', st.session_state.current_xrp, sell_p)
                        
                        # --- CALCULS NETS (Frais Kraken 0.26% x 2) ---
                        frais = 0.0026
                        valeur_vente_brute = st.session_state.current_xrp * sell_p
                        valeur_achat_brute = st.session_state.current_xrp * buy_p
                        
                        # Gain net en USD sur ce cycle précis
                        gain_cycle_usd = (valeur_vente_brute * (1-frais)) - (valeur_achat_brute * (1+frais))
                        
                        # Mise à jour du profit cumulé en USD
                        st.session_state.total_gain_usd += gain_cycle_usd
                        
                        # Effet Boule de Neige : On rachète plus de XRP pour le prochain tour
                        nouveau_stock_xrp = ((valeur_vente_brute * (1-frais)) / buy_p) * (1-frais)
                        st.session_state.current_xrp = nouveau_stock_xrp
                        
                        st.success(f"💰 Cycle validé ! Gain : +{gain_cycle_usd:.2f} USD")
                        time.sleep(2)
                        st.rerun()
                        break
                    time.sleep(20)
            
            time.sleep(20)

        except Exception as e:
            st.error(f"Erreur : {e}")
            time.sleep(60)
