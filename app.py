import streamlit as st
import ccxt
import os
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="XRP Snowball Bot", layout="wide")
st.title("🤖 Bot XRP/USDC - Kraken (Boule de Neige)")

# --- RÉCUPÉRATION DES SECRETS ---
# Sur Streamlit Cloud : Settings > Secrets
API_KEY = st.secrets.get("KRAKEN_API_KEY")
API_SECRET = st.secrets.get("KRAKEN_API_SECRET")

if not API_KEY or not API_SECRET:
    st.error("⚠️ Clés API Kraken manquantes dans les Secrets Streamlit !")
    st.stop()

# --- INITIALISATION KRAKEN ---
exchange = ccxt.kraken({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

# --- PARAMÈTRES DU BOT ---
SYMBOL = 'XRP/USDC'
STAKE_AMOUNT = 20.0    # Premier achat en USDC
MULTIPLIER = 1.5       # Facteur boule de neige
DIP_THRESHOLD = 0.02   # Rachat si baisse de 2%
PROFIT_TARGET = 0.03   # Vente à +3%

# --- FONCTIONS UTILES ---
def get_status():
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        balance = exchange.fetch_balance()
        return ticker['last'], balance['free'].get('XRP', 0), balance['free'].get('USDC', 0)
    except Exception as e:
        st.error(f"Erreur Kraken : {e}")
        return None, None, None

# --- INTERFACE UTILISATEUR ---
col1, col2, col3 = st.columns(3)

price, xrp_bal, usdc_bal = get_status()

if price:
    col1.metric("Prix XRP", f"{price} USDC")
    col2.metric("Solde XRP", f"{xrp_bal:.2f}")
    col3.metric("Solde USDC", f"{usdc_bal:.2f}")

st.divider()

# --- LOGIQUE DE TRADING (BOULE DE NEIGE) ---
if st.button("Démarrer la surveillance (Live)"):
    st.info("Le bot est en mode surveillance...")
    
    # Simulation d'état (Dans une app réelle, utilisez une base de données)
    last_buy_price = price
    
    status_placeholder = st.empty()
    
    while True:
        current_price, xrp_bal, usdc_bal = get_status()
        profit_pct = (current_price - last_buy_price) / last_buy_price
        
        status_placeholder.write(f"⏱️ Analyse... Profit actuel : {profit_pct:.2%}")

        # VENTE (Take Profit)
        if profit_pct >= PROFIT_TARGET and xrp_bal > 5:
            st.success(f"🚀 Vente détectée à {current_price} !")
            # exchange.create_market_sell_order(SYMBOL, xrp_bal)
            break

        # ACHAT (Boule de neige)
        elif profit_pct <= -DIP_THRESHOLD and usdc_bal > 10:
            st.warning(f"❄️ Effet Boule de neige : Achat supplémentaire !")
            # exchange.create_market_buy_order(SYMBOL, STAKE_AMOUNT / current_price)
            last_buy_price = current_price # Nouveau prix moyen
            
        time.sleep(60) # Attendre 1 minute
