import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Kraken XRP Bot", page_icon="🪙")
st.title("🤖 Bot XRP/USDC Kraken")

# Connexion sécurisée via Streamlit Secrets
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    st.success("Connecté à Kraken")
except:
    st.error("Erreur de connexion : Vérifie tes API Keys dans les Secrets.")

# --- CONFIGURATION ---
SYMBOL = 'XRP/USDC'
QUANTITE = st.number_input("Quantité de XRP à trader", value=30)
PROFIT_CIBLE = st.number_input("Profit cible (USDC)", value=0.02, format="%.3f")

# --- INTERFACE DE LOG ---
st.subheader("Activité du Bot")
log_window = st.empty()
prix_display = st.empty()

if st.button("Lancer le cycle de trading"):
    st.info("Bot démarré. Ne ferme pas cet onglet.")
    
    while True:
        try:
            # 1. Analyse du prix
            ticker = exchange.fetch_ticker(SYMBOL)
            prix_actuel = ticker['last']
            prix_vente_cible = prix_actuel + PROFIT_CIBLE
            
            prix_display.metric("Prix Actuel", f"{prix_actuel} USDC", delta=f"Cible: {prix_vente_cible}")

            # 2. Logique d'Achat
            log_window.write(f"🛒 Tentative d'achat à {prix_actuel}...")
            # exchange.create_market_buy_order(SYMBOL, QUANTITE)
            log_window.write(f"✅ Achat fait ! Attente de revente à {prix_vente_cible}...")

            # 3. Boucle d'attente de revente
            vendu = False
            while not vendu:
                ticker = exchange.fetch_ticker(SYMBOL)
                prix_actuel = ticker['last']
                prix_display.metric("Prix Actuel", f"{prix_actuel} USDC", delta=f"{prix_actuel - prix_vente_cible:.4f}")
                
                if prix_actuel >= prix_vente_cible:
                    log_window.write(f"💰 Cible atteinte ({prix_actuel}) ! Vente en cours...")
                    # exchange.create_market_sell_order(SYMBOL, QUANTITE)
                    log_window.write("🚀 Vente terminée. Redémarrage du cycle dans 1 min.")
                    vendu = True
                    time.sleep(60)
                
                time.sleep(10) # Rafraîchissement court pour Streamlit

        except Exception as e:
            st.error(f"Erreur : {e}")
            time.sleep(30)
