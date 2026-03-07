import streamlit as st
import ccxt
import time
from datetime import datetime

st.set_page_config(page_title="XRP Net Bot", layout="centered")
st.title("💰 XRP Net : Boule de Neige")

# --- CONFIGURATION ---
with st.container():
    col1, col2 = st.columns(2)
    buy_p = col1.number_input("Prix d'Achat (USD)", value=2.50, format="%.4f")
    sell_p = col2.number_input("Prix de Vente (USD)", value=2.60, format="%.4f")
    amount_init = st.number_input("Montant de départ (XRP)", value=20.0)

# Connexion API (via Secrets Streamlit)
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_API_KEY"],
    'secret': st.secrets["KRAKEN_SECRET"],
    'enableRateLimit': True,
})

# Initialisation du capital net
if 'current_qty' not in st.session_state:
    st.session_state.current_qty = amount_init

# --- AFFICHAGE DES GAINS NETS ---
st.write("---")
c1, c2 = st.columns(2)
c1.metric("Stock XRP Net", f"{st.session_state.current_qty:.2f} XRP")
profit_net = st.session_state.current_qty - amount_init
c2.metric("Gain Net Accumulé", f"+{profit_net:.2f} XRP", delta=f"{profit_net:.4f}")

status = st.empty()
log_area = st.container()

# --- LOGIQUE DU BOT ---
if st.button("Lancer le Bot (Gain Net)"):
    st.info("Surveillance du marché activée...")
    
    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USD')
            prix_actuel = ticker['last']
            status.markdown(f"**Prix actuel :** `{prix_actuel}$` | **Cible :** `{buy_p}$`")

            # 1. ACHAT NET
            if prix_actuel <= buy_p:
                status.warning("🛒 Exécution de l'achat...")
                # exchange.create_limit_buy_order('XRP/USD', st.session_state.current_qty, buy_p)
                
                # 2. VENTE ET CALCUL NET (Boule de neige)
                status.warning("⏳ Achat fait. Attente du prix de vente...")
                while True:
                    p = exchange.fetch_ticker('XRP/USD')['last']
                    if p >= sell_p:
                        # exchange.create_limit_sell_order('XRP/USD', st.session_state.current_qty, sell_p)
                        
                        # Calcul Net après 0.26% de frais à l'achat ET à la vente
                        frais = 0.0026
                        # On réinvestit tout le capital net restant
                        nouveau_net = ((st.session_state.current_qty * sell_p * (1-frais)) / buy_p) * (1-frais)
                        
                        st.session_state.current_qty = nouveau_net
                        st.success(f"✅ Cycle terminé ! Nouveau solde net : {nouveau_net:.2f} XRP")
                        time.sleep(2)
                        st.rerun() # Mise à jour immédiate de l'affichage
                        break
                    time.sleep(15)
            
            time.sleep(15)

        except Exception as e:
            st.error(f"Erreur API : {e}")
            time.sleep(30)

# Historique simple
with log_area:
    st.write("---")
    st.write("🕒 **Dernière mise à jour :**", datetime.now().strftime("%H:%M:%S"))
