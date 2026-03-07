import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Bot XRP Kraken REEL", layout="centered")
st.title("🚀 Bot XRP Kraken : ORDRES RÉELS")

# --- CONNEXION KRAKEN (Secrets) ---
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
except Exception as e:
    st.error("Erreur de clés API. Vérifiez vos Secrets Streamlit.")
    st.stop()

# --- CONFIGURATION INTERFACE ---
with st.container():
    col1, col2 = st.columns(2)
    buy_p = col1.number_input("Prix d'Achat (USD)", value=1.3500, format="%.4f")
    sell_p = col2.number_input("Prix de Vente (USD)", value=1.3700, format="%.4f")
    usdc_init = st.number_input("Montant à investir (USDC)", value=25.0)

# Initialisation des variables de session
if 'current_usdc' not in st.session_state:
    st.session_state.current_usdc = usdc_init
if 'total_gain_usdc' not in st.session_state:
    st.session_state.total_gain_usdc = 0.0

# --- AFFICHAGE DES SCORES ---
st.write("---")
c1, c2 = st.columns(2)
c1.metric("Capital Actuel", f"{st.session_state.current_usdc:.2f} USDC")
c2.metric("Gain Net Accumulé", f"+{st.session_state.total_gain_usdc:.2f} USDC")

status = st.empty()

# --- BOUCLE DE TRADING RÉEL ---
if st.button("🚀 LANCER LE BOT (ORDRES RÉELS)"):
    st.session_state.current_usdc = usdc_init
    st.warning("⚡ Bot en ligne sur Kraken. Surveillance en cours...")

    while True:
        try:
            # Récupération du prix actuel (Paire XRP/USDC)
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_actuel = ticker['last']
            status.info(f"🔍 Prix Marché : {prix_actuel}$ | Cible Achat : {buy_p}$")

            # 1. PHASE ACHAT RÉEL
            if prix_actuel <= buy_p:
                frais = 0.0026
                qty = (st.session_state.current_usdc * (1 - frais)) / buy_p
                
                status.warning(f"🛒 ENVOI ORDRE ACHAT : {qty:.2f} XRP à {buy_p}$")
                
                # --- EXECUTION RÉELLE SUR KRAKEN ---
                order_buy = exchange.create_limit_buy_order('XRP/USDC', qty, buy_p)
                st.success(f"✅ Ordre Achat envoyé ! ID: {order_buy['id']}")

                # 2. PHASE ATTENTE VENTE RÉELLE
                status.warning("⏳ Achat exécuté. Attente du prix de vente...")
                while True:
                    p_ticker = exchange.fetch_ticker('XRP/USDC')
                    p_actuel = p_ticker['last']
                    
                    if p_actuel >= sell_p:
                        status.warning(f"💰 ENVOI ORDRE VENTE : {qty:.2f} XRP à {sell_p}$")
                        
                        # --- EXECUTION RÉELLE SUR KRAKEN ---
                        order_sell = exchange.create_limit_sell_order('XRP/USDC', qty, sell_p)
                        
                        # Calcul Boule de Neige (Gain Net)
                        nouveau_total = (qty * sell_p) * (1 - frais)
                        gain_cycle = nouveau_total - st.session_state.current_usdc
                        
                        st.session_state.total_gain_usdc += gain_cycle
                        st.session_state.current_usdc = nouveau_total
                        
                        st.success(f"✨ Vente terminée ! Profit : +{gain_cycle:.2f} USDC")
                        time.sleep(10)
                        st.rerun() # Relance le cycle avec le nouveau capital
                        break
                    time.sleep(30) # Vérification vente toutes les 30s

            time.sleep(30) # Vérification achat toutes les 30s

        except Exception as e:
            st.error(f"❌ Erreur Kraken : {e}")
            time.sleep(60)
