import streamlit as st
import ccxt
import time
from datetime import datetime

st.set_page_config(page_title="XRP USDC Profit Bot", layout="centered")
st.title("🤖 XRP Boule de Neige (USDC)")

# --- CONFIGURATION (Interface) ---
with st.container():
    col_p1, col_p2 = st.columns(2)
    buy_p = col_p1.number_input("Prix d'Achat XRP (USD)", value=2.50, format="%.4f")
    sell_p = col_p2.number_input("Prix de Vente XRP (USD)", value=2.60, format="%.4f")
    usdc_init = st.number_input("Montant de départ (USDC)", value=50.00, step=10.0)

# Connexion API Kraken
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
except:
    st.error("⚠️ Clés API manquantes dans les Secrets Streamlit.")
    st.stop()

# Initialisation des variables de session
if 'current_usdc' not in st.session_state:
    st.session_state.current_usdc = usdc_init
if 'total_gain_usdc' not in st.session_state:
    st.session_state.total_gain_usdc = 0.0

# --- AFFICHAGE DES SCORES ---
st.write("---")
c1, c2 = st.columns(2)
c1.metric("Capital USDC Net", f"{st.session_state.current_usdc:.2f} USDC")
c2.metric("Gain Net Accumulé", f"+{st.session_state.total_gain_usdc:.2f} USDC")

# --- SÉCURITÉ : CALCUL DE RENTABILITÉ ---
frais_taux = 0.0026 # 0.26% chez Kraken
seuil_rentabilite = (buy_p * (1 + frais_taux)) / (1 - frais_taux)

if sell_p <= seuil_rentabilite:
    st.error(f"❌ Stratégie perdante ! Pour un achat à {buy_p}, vendez au minimum à {seuil_rentabilite:.4f} pour couvrir les frais.")
    bouton_actif = False
else:
    st.success(f"✅ Stratégie rentable. Gain estimé par cycle : {((sell_p/buy_p - 1) - (frais_taux*2))*100:.2f}%")
    bouton_actif = True

status = st.empty()

# --- LANCEMENT DU BOT ---
if bouton_actif and st.button("🚀 LANCER LE BOT"):
    st.info("Bot en cours d'exécution... Ne fermez pas cette page.")
    
    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USD')
            prix_actuel = ticker['last']
            status.markdown(f"**Prix actuel :** `{prix_actuel}$` | **Cible Achat :** `{buy_p}$`")

            # 1. PHASE ATTENTE ACHAT
            if prix_actuel <= buy_p:
                status.warning("🛒 Prix d'achat atteint. Calcul du montant...")
                
                # Combien de XRP on achète avec notre capital USDC actuel
                qty_to_buy = (st.session_state.current_usdc * (1 - frais_taux)) / buy_p
                
                # exchange.create_limit_buy_order('XRP/USD', qty_to_buy, buy_p)
                status.warning(f"✅ Achat de {qty_to_buy:.2f} XRP effectué. Attente vente à {sell_p}$...")

                # 2. PHASE ATTENTE VENTE
                while True:
                    p = exchange.fetch_ticker('XRP/USD')['last']
                    if p >= sell_p:
                        # exchange.create_limit_sell_order('XRP/USD', qty_to_buy, sell_p)
                        
                        # Calcul du retour final en USDC
                        nouveau_total_usdc = (qty_to_buy * sell_p) * (1 - frais_taux)
                        gain_du_cycle = nouveau_total_usdc - st.session_state.current_usdc
                        
                        # Mise à jour Boule de Neige
                        st.session_state.total_gain_usdc += gain_du_cycle
                        st.session_state.current_usdc = nouveau_total_usdc
                        
                        st.success(f"💰 Vente réussie ! Gain : +{gain_du_cycle:.2f} USDC")
                        time.sleep(5)
                        st.rerun() # Relance la boucle avec le nouveau capital
                        break
                    time.sleep(20)
            
            time.sleep(20)

        except Exception as e:
            st.error(f"Erreur API : {e}")
            time.sleep(60)
