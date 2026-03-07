import streamlit as st
import ccxt
import time

st.set_page_config(page_title="XRP Sniper Bot", page_icon="🤖")
st.title("🤖 Bot XRP/USDC Opérationnel")

# 1. Connexion (déjà testée avec succès !)
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_KEY"],
    'secret': st.secrets["KRAKEN_SECRET"],
    'enableRateLimit': True,
    'options': {'nonce': lambda: int(time.time() * 1000)}
})

# 2. Configuration du Trade
st.sidebar.header("Réglages du Bot")
p_achat = st.sidebar.number_input("Prix Achat (USDC)", value=1.3000, format="%.4f")
p_vente = st.sidebar.number_input("Prix Vente (USDC)", value=1.4000, format="%.4f")
montant = st.sidebar.number_input("Montant (XRP)", value=20.0, step=1.0)

# 3. Lancement de la boucle
if st.button("▶️ Démarrer la Surveillance Automatique"):
    status = st.empty()
    prix_live = st.empty()
    etape = "ATTENTE_ACHAT" # On commence par chercher à acheter
    
    st.warning("⚠️ Bot actif. Ne ferme pas cette page pour continuer le trading.")
    
    while etape != "FINI":
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            actuel = ticker['last']
            
            if etape == "ATTENTE_ACHAT":
                prix_live.metric("Prix XRP", f"{actuel} USDC", f"Cible Achat: {p_achat}")
                status.info(f"⏳ En attente du prix d'achat : {p_achat} USDC...")
                if actuel <= p_achat:
                    status.warning("🛒 Prix atteint ! Achat au marché...")
                    exchange.create_market_buy_order('XRP/USDC', montant)
                    st.success(f"✅ Achat réussi à {actuel} !")
                    etape = "ATTENTE_VENTE"
                    time.sleep(10) # Pause de sécurité
            
            elif etape == "ATTENTE_VENTE":
                prix_live.metric("Prix XRP", f"{actuel} USDC", f"Cible Vente: {p_vente}")
                status.info(f"🚀 XRP en main. En attente de vente à {p_vente} USDC...")
                if actuel >= p_vente:
                    status.warning("💰 Cible atteinte ! Vente au marché...")
                    exchange.create_market_sell_order('XRP/USDC', montant)
                    st.success(f"💎 Vente terminée avec profit !")
                    st.balloons()
                    etape = "FINI"

            time.sleep(10) # Vérifie toutes les 10 secondes
            
        except Exception as e:
            st.error(f"⚠️ Une erreur est survenue : {e}")
            break

if st.button("🛑 Arrêter le Bot"):
    st.experimental_rerun()
