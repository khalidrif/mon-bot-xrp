import streamlit as st
import ccxt
import time

st.set_page_config(page_title="XRP Profit Bot", page_icon="💰")
st.title("💰 Bot XRP : Cycle & Gain Brut")

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

# 2. Configuration
st.sidebar.header("💵 Paramètres Financiers")
budget_usdc = st.sidebar.number_input("Budget Achat (USDC)", value=30.0, min_value=15.0)
p_achat_cible = st.sidebar.number_input("Prix ACHAT (USDC)", value=1.3000, format="%.4f")
p_vente_cible = st.sidebar.number_input("Prix VENTE (USDC)", value=1.3500, format="%.4f")

# Initialisation des variables de session pour le profit
if 'total_gain' not in st.session_state:
    st.session_state.total_gain = 0.0
if 'dernier_achat_cout' not in st.session_state:
    st.session_state.dernier_achat_cout = 0.0

# 3. Interface de suivi
col1, col2 = st.columns(2)
prix_live = col1.empty()
gain_display = col2.metric("Gain Brut Total", f"{st.session_state.total_gain:.4f} USDC")
status = st.empty()
log_area = st.container()

if st.button("▶️ LANCER LE BOT"):
    st.warning("Bot actif. Surveillance en cours...")
    etape = "ACHAT"
    
    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_actuel = ticker['last']
            prix_live.metric("Prix XRP actuel", f"{prix_actuel} USDC")

            # --- PHASE D'ACHAT ---
            if etape == "ACHAT":
                status.info(f"⏳ Attente Achat à {p_achat_cible} USDC...")
                if prix_actuel <= p_achat_cible:
                    quantite_xrp = (budget_usdc * 0.995) / prix_actuel
                    status.warning(f"🎯 Achat de {quantite_xrp:.2f} XRP...")
                    
                    ordre = exchange.create_market_buy_order('XRP/USDC', quantite_xrp)
                    
                    # On mémorise le coût réel de cet achat
                    st.session_state.dernier_achat_cout = quantite_xrp * prix_actuel
                    
                    with log_area:
                        st.write(f"✅ **ACHAT** : {quantite_xrp:.2f} XRP à {prix_actuel} USDC (Coût: {st.session_state.dernier_achat_cout:.2f})")
                    etape = "VENTE"
                    time.sleep(10)

            # --- PHASE DE VENTE ---
            elif etape == "VENTE":
                status.info(f"🚀 Attente Vente à {p_vente_cible} USDC...")
                if prix_actuel >= p_vente_cible:
                    bal = exchange.fetch_balance()
                    total_xrp = bal.get('XRP', {}).get('free', 0)
                    
                    status.warning(f"💰 Vente de {total_xrp:.2f} XRP...")
                    ordre = exchange.create_market_sell_order('XRP/USDC', total_xrp)
                    
                    # Calcul du gain du cycle
                    valeur_vente = total_xrp * prix_actuel
                    gain_cycle = valeur_vente - st.session_state.dernier_achat_cout
                    st.session_state.total_gain += gain_cycle
                    
                    # Mise à jour de l'affichage du gain
                    gain_display.metric("Gain Brut Total", f"{st.session_state.total_gain:.4f} USDC", f"+{gain_cycle:.4f}")
                    
                    with log_area:
                        st.success(f"💎 **VENTE** : {total_xrp:.2f} XRP à {prix_actuel} USDC")
                        st.info(f"📈 **Gain sur ce cycle** : {gain_cycle:.4f} USDC")
                    
                    st.balloons()
                    etape = "ACHAT"
                    time.sleep(10)

            time.sleep(10)

        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            time.sleep(30)
