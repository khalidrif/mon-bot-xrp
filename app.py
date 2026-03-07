import streamlit as st
import ccxt
import time

st.set_page_config(page_title="XRP Profit Bot", layout="centered")
st.title("🤖 XRP Boule de Neige")

# --- CONFIGURATION (Barre latérale) ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    buy_p = st.number_input("Prix d'Achat (USD)", value=2.50, format="%.4f")
    sell_p = st.number_input("Prix de Vente (USD)", value=2.60, format="%.4f")
    initial_amount = st.number_input("Montant Départ (XRP)", value=20.00)

# Connexion Kraken sécurisée
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
except Exception as e:
    st.error("Erreur de clés API. Vérifiez vos 'Secrets' sur Streamlit.")
    st.stop()

# Initialisation des variables de session
if 'current_xrp' not in st.session_state:
    st.session_state.current_xrp = initial_amount
if 'total_gain_usd' not in st.session_state:
    st.session_state.total_gain_usd = 0.0

# --- AFFICHAGE DES SCORES (Corrigé) ---
c1, c2 = st.columns(2)

with c1:
    st.metric("Capital Actuel", f"{st.session_state.current_xrp:.2f} XRP")

with c2:
    # Affiche le profit net accumulé en USD
    st.metric("Gain Net Accumulé", f"+{st.session_state.total_gain_usd:.2f} USD")

status = st.empty()

# --- LOGIQUE DU BOT ---
if st.button("Démarrer le Cycle"):
    st.toast("Bot lancé avec succès !")
    
    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USD')
            prix_actuel = ticker['last']
            status.info(f"🔍 Prix Marché : {prix_actuel}$ | Cible Achat : {buy_p}$")

            # 1. PHASE ATTENTE ACHAT
            if prix_actuel <= buy_p:
                status.warning("🛒 Prix d'achat atteint. Exécution...")
                # exchange.create_limit_buy_order('XRP/USD', st.session_state.current_xrp, buy_p)
                
                # 2. PHASE ATTENTE VENTE
                status.warning("⏳ Achat validé. Attente du prix de vente...")
                while True:
                    p = exchange.fetch_ticker('XRP/USD')['last']
                    if p >= sell_p:
                        # exchange.create_limit_sell_order('XRP/USD', st.session_state.current_xrp, sell_p)
                        
                        # --- CALCULS NETS (Frais 0.26% x 2) ---
                        frais = 0.0026
                        val_vente_brute = st.session_state.current_xrp * sell_p
                        val_achat_brute = st.session_state.current_xrp * buy_p
                        
                        # Gain net en USD sur ce cycle
                        gain_cycle_usd = (val_vente_brute * (1-frais)) - (val_achat_brute * (1+frais))
                        st.session_state.total_gain_usd += gain_cycle_usd
                        
                        # Boule de Neige : réinvestissement pour augmenter le stock de XRP
                        nouveau_stock = ((val_vente_brute * (1-frais)) / buy_p) * (1-frais)
                        st.session_state.current_xrp = nouveau_stock
                        
                        st.success(f"💰 Vente réussie ! Gain : +{gain_cycle_usd:.2f} USD")
                        time.sleep(2)
                        st.rerun() # Rafraîchit les chiffres en haut
                        break
                    time.sleep(20)
            
            time.sleep(20)

        except Exception as e:
            st.error(f"Erreur API : {e}")
            time.sleep(60)
