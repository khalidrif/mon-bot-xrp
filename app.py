import streamlit as st
import ccxt
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Sniper Bot", layout="wide")
st.title("🤖 Bot XRP - Achat/Vente Automatique")

# Connexion Kraken
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
    })
    symbol = "XRP/USDC"
except Exception as e:
    st.error(f"Erreur API : {e}")
    st.stop()

# --- MÉMOIRE ---
if 'actif' not in st.session_state:
    st.session_state.actif = False
if 'etape' not in st.session_state:
    st.session_state.etape = "ATTENTE_ACHAT"

# --- RÉGLAGES ---
with st.sidebar:
    st.header("⚙️ Stratégie")
    p_achat = st.number_input("Prix ACHAT (LIMIT)", value=1.3620, format="%.4f")
    p_vente = st.number_input("Prix VENTE (LIMIT)", value=1.3850, format="%.4f")
    mise_usdc = st.number_input("Mise (USDC)", min_value=10.0, value=20.0)
    
    st.divider()
    st.write(f"Prochaine action : **{st.session_state.etape}**")
    if st.button("🔄 Reset à ACHAT"):
        st.session_state.etape = "ATTENTE_ACHAT"
        st.rerun()

# --- BOUTONS ---
c1, c2 = st.columns(2)
if c1.button("🚀 LANCER LA BOUCLE", type="primary", use_container_width=True):
    st.session_state.actif = True
if c2.button("🛑 STOP", use_container_width=True):
    st.session_state.actif = False

# --- LOGIQUE DE TRADING ---
if st.session_state.actif:
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        usdc_bal = bal['free'].get('USDC', 0.0)
        xrp_bal = bal['free'].get('XRP', 0.0)

        st.metric("Prix XRP actuel", f"{price:.4f} USDC")

        # 1. ÉTAPE ACHAT
        if st.session_state.etape == "ATTENTE_ACHAT" and price <= p_achat:
            if usdc_bal >= mise_usdc:
                st.warning(f"⚡ Exécution : ACHAT LIMIT à {p_achat}")
                qty = float(exchange.amount_to_precision(symbol, mise_usdc / p_achat))
                
                # On place l'achat
                exchange.create_limit_buy_order(symbol, qty, p_achat)
                
                # ON PASSE DIRECTEMENT À LA VENTE
                st.session_state.etape = "ATTENTE_VENTE"
                st.success("✅ Achat envoyé. Passage en mode VENTE.")
                time.sleep(5) 
                st.rerun()

        # 2. ÉTAPE VENTE
        elif st.session_state.etape == "ATTENTE_VENTE" and price >= p_vente:
            if xrp_bal > 5:
                st.info(f"💰 Exécution : VENTE LIMIT à {p_vente}")
                qty_sell = float(exchange.amount_to_precision(symbol, xrp_bal * 0.995))
                
                # On place la vente
                exchange.create_limit_sell_order(symbol, qty_sell, p_vente)
                
                # ON REVIENT À L'ACHAT POUR LA PROCHAINE FOIS
                st.session_state.etape = "ATTENTE_ACHAT"
                st.balloons()
                time.sleep(10)
                st.rerun()

        time.sleep(15)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur : {e}")
        time.sleep(20)
        st.rerun()
