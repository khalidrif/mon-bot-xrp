import streamlit as st
import ccxt
import time
from datetime import datetime

st.set_page_config(page_title="XRP/USDC Real Bot", layout="centered")
st.title("🚀 Bot XRP Kraken : Ordres Réels (USDC)")

# --- CONNEXION KRAKEN (Secrets) ---
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
except Exception as e:
    st.error("🔑 Erreur API : Vérifiez vos Secrets Streamlit (API Key et Secret).")
    st.stop()

# --- CONFIGURATION ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    buy_p = st.number_input("Prix d'Achat (USD)", value=1.3500, format="%.4f")
    sell_p = st.number_input("Prix de Vente (USD)", value=1.3700, format="%.4f")
    usdc_init = st.number_input("Montant Départ (USDC)", value=30.00, step=5.0)
    st.info("💡 Kraken impose un minimum d'environ 15 XRP par ordre.")

# Initialisation des variables de session
if 'current_usdc' not in st.session_state:
    st.session_state.current_usdc = usdc_init
if 'total_gain_usdc' not in st.session_state:
    st.session_state.total_gain_usdc = 0.0

# --- AFFICHAGE DES GAINS NETS ---
st.write("---")
c1, c2 = st.columns(2)
c1.metric("Capital USDC Net", f"{st.session_state.current_usdc:.2f} USDC")
c2.metric("Gain Net Accumulé", f"+{st.session_state.total_gain_usdc:.2f} USDC")

status = st.empty()

# --- LOGIQUE DU BOT ---
if st.button("🚀 LANCER LE BOT (ORDRES RÉELS)"):
    st.session_state.current_usdc = usdc_init
    st.warning("⚡ Bot en ligne sur Kraken. Ne fermez pas cette page.")

    while True:
        try:
            # 1. Vérification du prix actuel
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_actuel = ticker['last']
            status.info(f"🔍 Prix : {prix_actuel}$ | Cible Achat : {buy_p}$")

            # 2. PHASE ACHAT RÉEL
            if prix_actuel <= buy_p:
                frais = 0.0026
                qty = (st.session_state.current_usdc * (1 - frais)) / buy_p
                
                status.warning(f"🛒 Envoi ORDRE ACHAT : {qty:.2f} XRP à {buy_p}$")
                
                # EXECUTION RÉELLE
                order_buy = exchange.create_limit_buy_order('XRP/USDC', qty, buy_p)
                st.success(f"✅ Achat envoyé ! ID: {order_buy['id']}")

                # 3. PHASE ATTENTE VENTE RÉELLE
                while True:
                    p_ticker = exchange.fetch_ticker('XRP/USDC')
                    if p_ticker['last'] >= sell_p:
                        status.warning(f"💰 Envoi ORDRE VENTE : {qty:.2f} XRP à {sell_p}$")
                        
                        # EXECUTION RÉELLE
                        order_sell = exchange.create_limit_sell_order('XRP/USDC', qty, sell_p)
                        
                        # Calcul Boule de Neige
                        nouveau_total = (qty * sell_p) * (1 - frais)
                        gain_cycle = nouveau_total - st.session_state.current_usdc
                        
                        st.session_state.total_gain_usdc += gain_cycle
                        st.session_state.current_usdc = nouveau_total
                        
                        st.balloons()
                        st.success(f"✨ Cycle Terminé ! Profit : +{gain_cycle:.2f} USDC")
                        time.sleep(10)
                        st.rerun() 
                        break
                    time.sleep(20) # Check vente toutes les 20s

            time.sleep(20) # Check achat toutes les 20s

        except Exception as e:
            st.error(f"❌ Erreur Kraken : {e}")
            time.sleep(60)
