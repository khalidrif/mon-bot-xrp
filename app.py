import streamlit as st
import ccxt
import time
from datetime import datetime

st.set_page_config(page_title="XRP Net Bot", layout="centered")
st.title("💰 XRP Net : Boule de Neige")

# --- CONFIGURATION ---
with st.container():
    col_p1, col_p2 = st.columns(2)
    buy_p = col_p1.number_input("Prix d'Achat (USD)", value=2.50, format="%.4f")
    sell_p = col_p2.number_input("Prix de Vente (USD)", value=2.60, format="%.4f")
    amount_init = st.number_input("Montant de départ (XRP)", value=20.00)

# Connexion API (via Secrets Streamlit)
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_API_KEY"],
    'secret': st.secrets["KRAKEN_SECRET"],
    'enableRateLimit': True,
})

# Initialisation des variables de session
if 'current_qty' not in st.session_state:
    st.session_state.current_qty = amount_init
if 'total_gain_usd' not in st.session_state:
    st.session_state.total_gain_usd = 0.0

# --- AFFICHAGE DES GAINS NETS ---
st.write("---")
c1, c2 = st.columns(2)

# Affiche le stock de XRP qui grossit (Boule de neige)
c1.metric("Stock XRP Net", f"{st.session_state.current_qty:.2f} XRP")

# Affiche le profit net accumulé en USD
c2.metric("Gain Net Accumulé", f"+{st.session_state.total_gain_usd:.2f} USD")

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

            # 1. PHASE ATTENTE ACHAT
            if prix_actuel <= buy_p:
                status.warning("🛒 Prix d'achat atteint. Exécution de l'achat...")
                # exchange.create_limit_buy_order('XRP/USD', st.session_state.current_qty, buy_p)
                
                # 2. PHASE ATTENTE VENTE
                status.warning("⏳ Achat fait. Attente du prix de vente...")
                while True:
                    p = exchange.fetch_ticker('XRP/USD')['last']
                    if p >= sell_p:
                        # exchange.create_limit_sell_order('XRP/USD', st.session_state.current_qty, sell_p)
                        
                        # --- CALCULS NETS (Frais Kraken 0.26% x 2) ---
                        frais = 0.0026
                        valeur_vente_brute = st.session_state.current_qty * sell_p
                        valeur_achat_brute = st.session_state.current_qty * buy_p
                        
                        # Calcul du profit net en USD sur ce cycle
                        gain_cycle_usd = (valeur_vente_brute * (1-frais)) - (valeur_achat_brute * (1+frais))
                        st.session_state.total_gain_usd += gain_cycle_usd
                        
                        # Effet Boule de Neige : calcul du nouveau stock XRP réinvesti
                        nouveau_net_xrp = ((valeur_vente_brute * (1-frais)) / buy_p) * (1-frais)
                        st.session_state.current_qty = nouveau_net_xrp
                        
                        st.success(f"✅ Cycle terminé ! Gain : +{gain_cycle_usd:.2f} USD")
                        time.sleep(2)
                        st.rerun() # Met à jour les compteurs en haut
                        break
                    time.sleep(20)
            
            time.sleep(20)

        except Exception as e:
            st.error(f"Erreur API : {e}")
            time.sleep(60)

# Historique simple en bas
with log_area:
    st.write("---")
    st.write("🕒 **Dernière mise à jour :**", datetime.now().strftime("%H:%M:%S"))
