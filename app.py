import streamlit as st
import ccxt
import time

st.set_page_config(page_title="XRP Cycle Bot", page_icon="🔄")
st.title("🔄 Bot XRP/USDC : Cycle Achat ➔ Vente")

# 1. Connexion API avec correction Nonce
@st.cache_resource
def init_exchange():
    return ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: int(time.time() * 1000)}
    })

exchange = init_exchange()

# 2. Interface de configuration
st.sidebar.header("⚙️ Paramètres du Cycle")
p_achat_cible = st.sidebar.number_input("Prix d'ACHAT (USDC)", value=1.3000, format="%.4f")
p_vente_cible = st.sidebar.number_input("Prix de VENTE (USDC)", value=1.3500, format="%.4f")
montant_xrp = st.sidebar.number_input("Montant (XRP)", value=20.0, min_value=10.0)

# Affichage du solde
try:
    balance = exchange.fetch_balance()
    usdc = balance.get('USDC', {}).get('free', 0)
    xrp = balance.get('XRP', {}).get('free', 0)
    st.sidebar.divider()
    st.sidebar.write(f"Portefeuille : **{usdc:.2f} USDC** | **{xrp:.2f} XRP**")
except:
    st.sidebar.error("Erreur de lecture du solde")

# 3. Logique du Bot
if st.button("▶️ DÉMARRER LE CYCLE INFINI"):
    status = st.empty()
    prix_live = st.empty()
    log_area = st.container()
    
    # On détermine l'étape initiale selon le solde (si on a déjà du XRP, on commence par vendre)
    etape = "ACHAT" if xrp < montant_xrp else "VENTE"
    
    st.warning(f"Bot actif. Étape initiale : {etape}. Gardez cet onglet ouvert.")

    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_actuel = ticker['last']
            
            # Affichage temps réel
            prix_live.metric("Prix XRP actuel", f"{prix_actuel} USDC")

            # --- PHASE D'ACHAT ---
            if etape == "ACHAT":
                status.info(f"⏳ Attente ACHAT à {p_achat_cible} USDC...")
                if prix_actuel <= p_achat_cible:
                    status.warning("🎯 Cible achat touchée ! Envoi de l'ordre...")
                    ordre = exchange.create_market_buy_order('XRP/USDC', montant_xrp)
                    with log_area:
                        st.success(f"✅ ACHAT effectué à {prix_actuel} | ID: {ordre['id']}")
                    etape = "VENTE"
                    time.sleep(10)

            # --- PHASE DE VENTE ---
            elif etape == "VENTE":
                status.info(f"🚀 Attente VENTE à {p_vente_cible} USDC...")
                if prix_actuel >= p_vente_cible:
                    status.warning("💰 Cible vente touchée ! Envoi de l'ordre...")
                    ordre = exchange.create_market_sell_order('XRP/USDC', montant_xrp)
                    with log_area:
                        st.success(f"💎 VENTE effectuée à {prix_actuel} | ID: {ordre['id']}")
                    st.balloons()
                    etape = "ACHAT" # On recommence le cycle
                    time.sleep(10)

            time.sleep(10) # Pause entre les vérifications

        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            time.sleep(30) # Attend un peu avant de retenter en cas d'erreur réseau
