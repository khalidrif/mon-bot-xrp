import streamlit as st
import ccxt
import time
import pandas as pd

st.set_page_config(page_title="XRP Dashboard", layout="wide")

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

# Initialisation de l'historique dans la session
if 'history' not in st.session_state:
    st.session_state.history = []
if 'total_gain' not in st.session_state:
    st.session_state.total_gain = 0.0

# --- INTERFACE ---
st.title("🤖 XRP Sniper Dashboard")

# Ligne 1 : Les indicateurs clés
col1, col2, col3, col4 = st.columns(4)
prix_live = col1.empty()
solde_usdc = col2.empty()
gain_total = col3.metric("Gain Brut Total", f"{st.session_state.total_gain:.4f} USDC")
status_bot = col4.empty()

# Ligne 2 : Configuration et Logs
col_config, col_logs = st.columns([1, 2])

with col_config:
    st.subheader("⚙️ Réglages")
    budget = st.number_input("Budget (USDC)", value=30.0, min_value=15.0)
    p_achat = st.number_input("Prix ACHAT (USDC)", value=1.3000, format="%.4f")
    p_vente = st.number_input("Prix VENTE (USDC)", value=1.3500, format="%.4f")
    btn_start = st.button("▶️ LANCER LE BOT", use_container_width=True)

with col_logs:
    st.subheader("📜 Historique des Cycles")
    log_table = st.empty()

# --- LOGIQUE DU BOT ---
if btn_start:
    etape = "ACHAT"
    dernier_achat_cout = 0.0
    
    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix = ticker['last']
            
            # Mise à jour des indicateurs en haut
            prix_live.metric("Prix XRP", f"{prix} USDC")
            bal = exchange.fetch_balance()
            solde_usdc.metric("Solde Disponible", f"{bal.get('USDC', {}).get('free', 0):.2f} USDC")
            
            if etape == "ACHAT":
                status_bot.info("🔍 Mode : ATTENTE ACHAT")
                if prix <= p_achat:
                    # ACHAT
                    qte = (budget * 0.995) / prix
                    exchange.create_market_buy_order('XRP/USDC', qte)
                    dernier_achat_cout = qte * prix
                    etape = "VENTE"
                    st.session_state.history.append({"Action": "ACHAT", "Prix": prix, "Qte": qte, "Total": dernier_achat_cout})
                    time.sleep(5)

            elif etape == "VENTE":
                status_bot.warning("🚀 Mode : ATTENTE VENTE")
                if prix >= p_vente:
                    # VENTE
                    total_xrp = exchange.fetch_balance().get('XRP', {}).get('free', 0)
                    exchange.create_market_sell_order('XRP/USDC', total_xrp)
                    
                    # CALCUL GAIN
                    valeur_vendu = total_xrp * prix
                    gain_brut = valeur_vendu - dernier_achat_cout
                    st.session_state.total_gain += gain_brut
                    
                    # MAJ Interface
                    gain_total.metric("Gain Brut Total", f"{st.session_state.total_gain:.4f} USDC", f"+{gain_brut:.4f}")
                    st.session_state.history.append({"Action": "VENTE", "Prix": prix, "Qte": total_xrp, "Total": valeur_vendu})
                    st.balloons()
                    etape = "ACHAT"
                    time.sleep(5)

            # Mise à jour du tableau de logs
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history).tail(10) # 10 derniers
                log_table.table(df)

            time.sleep(10)

        except Exception as e:
            st.error(f"Erreur : {e}")
            time.sleep(20)
