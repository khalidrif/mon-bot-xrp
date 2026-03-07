import streamlit as st
import ccxt
import time

st.set_page_config(page_title="XRP Trader Bot", page_icon="📈")
st.title("🚀 Bot XRP/USDC Kraken")

# 1. Initialisation
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    st.success("✅ Connexion API configurée !")
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# 2. Paramètres de trading
col1, col2 = st.columns(2)
with col1:
    quantite = st.number_input("Nombre de XRP à acheter", value=20.0, step=1.0)
with col2:
    profit_vise = st.number_input("Profit visé par XRP (USDC)", value=0.015, format="%.3f")

# 3. Interface de suivi
prix_zone = st.empty()
log_zone = st.container()

if st.button("Démarrer le cycle Achat ➔ Vente"):
    st.info("Bot actif... Ne ferme pas cette page.")
    
    while True:
        try:
            # ÉTAPE 1 : RÉCUPÉRER LE PRIX POUR L'ACHAT
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_actuel = ticker['last']
            prix_vente_cible = prix_actuel + profit_vise
            
            prix_zone.metric("Prix XRP actuel", f"{prix_actuel} USDC", f"Cible : {prix_vente_cible}")
            
            # ÉTAPE 2 : ACHAT (Décommenter les lignes 'exchange' pour de vrai)
            with log_zone:
                st.write(f"🛒 **Achat** de {quantite} XRP à {prix_actuel} USDC...")
                # order_buy = exchange.create_market_buy_order('XRP/USDC', quantite)
                st.write(f"⏳ Attente que le prix atteigne **{prix_vente_cible}** pour revendre...")

            # ÉTAPE 3 : BOUCLE D'ATTENTE DE REVENTE
            vendu = False
            while not vendu:
                ticker = exchange.fetch_ticker('XRP/USDC')
                prix_actuel = ticker['last']
                prix_zone.metric("Prix XRP actuel", f"{prix_actuel} USDC", f"{prix_actuel - prix_vente_cible:.4f}")

                if prix_actuel >= prix_vente_cible:
                    with log_zone:
                        st.write(f"💰 **Cible atteinte !** Vente de {quantite} XRP à {prix_actuel} USDC.")
                        # order_sell = exchange.create_market_sell_order('XRP/USDC', quantite)
                        st.balloons()
                    vendu = True
                
                time.sleep(15) # Vérification toutes les 15 secondes

        except Exception as e:
            st.error(f"Erreur : {e}")
            time.sleep(60)
