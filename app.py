import streamlit as st
import ccxt
import time

st.set_page_config(page_title="XRP Auto-Quantité Bot", page_icon="⚖️")
st.title("⚖️ Bot XRP/USDC : Budget en USDC")

# 1. Connexion API
@st.cache_resource
def init_exchange():
    return ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: int(time.time() * 1000)}
    })

exchange = init_exchange()

# 2. Configuration (Saisie en USDC)
st.sidebar.header("💰 Configuration du Budget")
budget_usdc = st.sidebar.number_input("Budget par ACHAT (en USDC)", value=30.0, min_value=15.0)
p_achat_cible = st.sidebar.number_input("Prix d'ACHAT cible (USDC)", value=1.3000, format="%.4f")
p_vente_cible = st.sidebar.number_input("Prix de VENTE cible (USDC)", value=1.3500, format="%.4f")

# Affichage du solde réel
try:
    balance = exchange.fetch_balance()
    usdc_reel = balance.get('USDC', {}).get('free', 0)
    xrp_reel = balance.get('XRP', {}).get('free', 0)
    st.sidebar.divider()
    st.sidebar.write(f"Disponible : **{usdc_reel:.2f} USDC**")
except:
    st.sidebar.error("Erreur de lecture du solde")

# 3. Logique du Bot
if st.button("▶️ LANCER LE CYCLE"):
    status = st.empty()
    prix_live = st.empty()
    log_area = st.container()
    
    # Étape initiale : on achète si on a plus de USDC que de XRP
    etape = "ACHAT" if (usdc_reel > 10 and xrp_reel < 5) else "VENTE"
    st.warning(f"Démarrage en mode : {etape}")

    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_actuel = ticker['last']
            prix_live.metric("Prix XRP actuel", f"{prix_actuel} USDC")

            # --- PHASE D'ACHAT ---
            if etape == "ACHAT":
                status.info(f"⏳ Attente Achat à {p_achat_cible} USDC...")
                if prix_actuel <= p_achat_cible:
                    # CALCUL AUTOMATIQUE DU NOMBRE DE XRP
                    # On retire 0.5% pour être sûr que les frais passent
                    quantite_xrp = (budget_usdc * 0.995) / prix_actuel 
                    
                    status.warning(f"🎯 Cible atteinte ! Achat de {quantite_xrp:.2f} XRP...")
                    ordre = exchange.create_market_buy_order('XRP/USDC', quantite_xrp)
                    
                    with log_area:
                        st.success(f"✅ ACHAT : {quantite_xrp:.2f} XRP à {prix_actuel} USDC")
                    etape = "VENTE"
                    time.sleep(10)

            # --- PHASE DE VENTE ---
            elif etape == "VENTE":
                status.info(f"🚀 Attente Vente à {p_vente_cible} USDC...")
                if prix_actuel >= p_vente_cible:
                    # Pour la vente, on récupère le solde XRP actuel
                    bal = exchange.fetch_balance()
                    total_xrp = bal.get('XRP', {}).get('free', 0)
                    
                    status.warning(f"💰 Cible atteinte ! Vente de {total_xrp:.2f} XRP...")
                    ordre = exchange.create_market_sell_order('XRP/USDC', total_xrp)
                    
                    with log_area:
                        st.success(f"💎 VENTE : {total_xrp:.2f} XRP à {prix_actuel} USDC")
                    st.balloons()
                    etape = "ACHAT"
                    time.sleep(10)

            time.sleep(10)

        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            time.sleep(30)
