import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Kraken XRP Sniper", page_icon="🎯")
st.title("🎯 Bot XRP/USDC Kraken")

# 1. Connexion API
@st.cache_resource
def init_exchange():
    try:
        return ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
            'options': {'nonce': lambda: int(time.time() * 1000)}
        })
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

exchange = init_exchange()

# 2. Interface latérale (Solde)
if exchange:
    try:
        balance = exchange.fetch_balance()
        usdc_dispo = balance.get('USDC', {}).get('free', 0)
        st.sidebar.metric("Solde USDC", f"{usdc_dispo:.2f}")
    except:
        st.sidebar.error("Erreur lecture solde")

# 3. Paramètres
st.subheader("Configuration")
p_achat = st.number_input("Prix Achat (USDC)", value=1.3000, format="%.4f")
p_vente = st.number_input("Prix Vente (USDC)", value=1.3500, format="%.4f")
montant = st.number_input("Montant XRP", value=10.0, step=1.0)

# 4. Exécution
if st.button("Démarrer"):
    status = st.empty()
    etape = "ACHAT"
    
    while etape != "FINI":
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            actuel = ticker['last']
            
            if etape == "ACHAT" and actuel <= p_achat:
                exchange.create_market_buy_order('XRP/USDC', montant)
                etape = "VENTE"
            elif etape == "VENTE" and actuel >= p_vente:
                exchange.create_market_sell_order('XRP/USDC', montant)
                etape = "FINI"
            
            time.sleep(10)
        except Exception as e:
            st.error(f"Erreur : {e}")
            break
