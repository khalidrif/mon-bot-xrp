import streamlit as st
import ccxt
import time

# Configuration de la page
st.set_page_config(page_title="Kraken XRP Sniper", page_icon="🎯")
st.title("🎯 Kraken XRP/USDC Sniper Bot")

# 1. Connexion API avec correction du Nonce (millisecondes)
@st.cache_resource
def get_kraken_connection():
    try:
        exchange = ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
            'options': {
                'nonce': lambda: int(time.time() * 1000) # Correction Invalid Nonce
            }
        })
        return exchange
    except Exception as e:
        st.error(f"Erreur d'initialisation : {e}")
        return None

exchange = get_kraken_connection()

# 2. Vérification du Solde et Connexion
if exchange:
    try:
        balance = exchange.fetch_balance()
        usdc_free = balance.get('USDC', {}).get('free', 0)
        st.sidebar.success(f"Portefeuille : {usdc_free:.2f} USDC")
    except Exception as e:
        st.error(f"❌ Erreur API : {e}")
        st.stop()

# 3. Paramètres de Trading
st.subheader("⚙️ Configuration de l'Ordre")
col1, col2, col3 = st.columns(3)

with col1:
    p_achat = st.number_input("Prix d'Achat (USDC)", value=1.3000, format="%.4f")
with col2:
    p_vente = st.number_input("Prix de Vente (USDC)", value=1.3500, format="%.4f")
with col3:
    montant = st.number_input("Montant (XRP)", value=20.0, step=1.0)

# 4. Exécution du Bot
if st.button("🚀 Lancer le Cycle"):
    status = st.empty()
    prix_live = st.empty()
    
    # PHASE D'ACHAT
    etape = "ACHAT"
    st.info("Bot actif... Ne ferme pas cet onglet.")
    
    while etape != "TERMINE":
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            actuel = ticker['last']
            
            if etape == "ACHAT":
                prix_live.metric("Prix XRP Actuel", f"{actuel} USDC", f"Cible Achat: {p_achat}")
                status.info(f"⏳ En attente du prix d'achat : {p_achat} USDC...")
                
                if actuel <= p_achat:
                    status.warning("⚠️ Cible d'achat atteinte ! Envoi de l'ordre...")
                    # EXECUTION REELLE
                    ordre_a = exchange.create_market_buy_order('XRP/USDC', montant)
                    st.write("✅ Achat effectué :", ordre_a['id'])
                    etape = "VENTE"
                    time.sleep(5) # Pause de sécurité
            
            elif etape == "VENTE":
                prix_live.metric("Prix XRP Actuel", f"{actuel} USDC", f"Cible Vente: {p_vente}")
                status.info(f"🚀 XRP en main. En attente de revente à {p_vente} USDC...")
                
                if actuel >= p_vente:
                    status.warning("⚠️ Cible de vente atteinte ! Envoi de l'ordre...")
                    # EXECUTION REELLE
                    ordre_v = exchange.create_market_sell_order('XRP/USDC', montant)
                    st.write("✅ Vente effectuée :", ordre_v['id'])
                    st.balloons()
                    etape = "TERMINE"

            time.sleep(15) # Fréquence de vérification (15 sec)

        except Exception as e:
            st.error(f"Erreur pendant le cycle : {e}")
            break

    if etape == "TERMINE":
        st.success("🎯 Cycle Achat/Vente terminé avec succès !")
