import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Kraken XRP Sniper", page_icon="🎯")
st.title("🎯 Bot XRP/USDC : Achat & Vente Précis")

# 1. Connexion API
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    st.success("✅ Connecté à Kraken")
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# 2. Paramètres du Trade
st.subheader("Configuration de l'ordre")
col1, col2, col3 = st.columns(3)

with col1:
    prix_achat_declench = st.number_input("Prix d'achat (USDC)", value=1.300, format="%.4f")
with col2:
    prix_vente_declench = st.number_input("Prix de vente (USDC)", value=1.350, format="%.4f")
with col3:
    montant_xrp = st.number_input("Montant (XRP)", value=30.0, step=1.0)

# 3. Interface de suivi
prix_live = st.empty()
log_status = st.info("En attente de démarrage...")

if st.button("🚀 Démarrer le Bot"):
    st.warning("Bot actif. Ne ferme pas cette page !")
    
    # ÉTAPE 1 : ATTENTE DU PRIX D'ACHAT
    achete = False
    while not achete:
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_actuel = ticker['last']
            prix_live.metric("Prix XRP actuel", f"{prix_actuel} USDC", f"Cible Achat: {prix_achat_declench}")
            
            if prix_actuel <= prix_achat_declench:
                log_status.warning(f"🎯 Prix d'achat atteint ({prix_actuel}) ! Exécution de l'achat...")
                # COMMANDE RÉELLE
                exchange.create_market_buy_order('XRP/USDC', montant_xrp)
                st.balloons()
                achete = True
            else:
                log_status.info(f"⏳ En attente du prix d'achat ({prix_achat_declench})...")
            
            time.sleep(10)
        except Exception as e:
            st.error(f"Erreur Achat : {e}")
            time.sleep(30)

    # ÉTAPE 2 : ATTENTE DU PRIX DE VENTE
    vendu = False
    while not vendu:
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_actuel = ticker['last']
            prix_live.metric("Prix XRP actuel", f"{prix_actuel} USDC", f"Cible Vente: {prix_vente_declench}", delta_color="normal")
            
            if prix_actuel >= prix_vente_declench:
                log_status.warning(f"💰 Prix de vente atteint ({prix_actuel}) ! Exécution de la vente...")
                # COMMANDE RÉELLE
                exchange.create_market_sell_order('XRP/USDC', montant_xrp)
                st.success("✅ Cycle terminé avec succès !")
                vendu = True
            else:
                log_status.info(f"🚀 XRP acheté ! En attente du prix de vente ({prix_vente_declench})...")
            
            time.sleep(10)
        except Exception as e:
            st.error(f"Erreur Vente : {e}")
            time.sleep(30)
