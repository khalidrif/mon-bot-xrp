import streamlit as st
import ccxt
import time

# 1. CONFIGURATION ET SECRETS
st.set_page_config(page_title="XRP Snowball Bot", layout="centered")
st.title("🤖 Bot XRP/USDC - Kraken")

# Lecture automatique des secrets que tu as configurés
try:
    API_KEY = st.secrets["KRAKEN_API_KEY"]
    API_SECRET = st.secrets["KRAKEN_API_SECRET"]
    
    exchange = ccxt.kraken({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True
    })
except Exception as e:
    st.error("⚠️ Erreur : Vérifie tes Secrets Streamlit (Noms des clés).")
    st.stop()

# 2. ÉTAT DU BOT
if 'actif' not in st.session_state:
    st.session_state.actif = False

# 3. INTERFACE DE CONTRÔLE
col1, col2 = st.columns(2)
if col1.button("🚀 DÉMARRER LE BOT", type="primary", use_container_width=True):
    st.session_state.actif = True

if col2.button("🛑 ARRÊTER LE BOT", use_container_width=True):
    st.session_state.actif = False

st.divider()

# 4. BOUCLE DE TRADING
if st.session_state.actif:
    try:
        # Récupération des données
        ticker = exchange.fetch_ticker('XRP/USDC')
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp = bal['free'].get('XRP', 0)
        usdc = bal['free'].get('USDC', 0)

        # Affichage
        st.success("✅ SURVEILLANCE EN COURS...")
        c1, c2, c3 = st.columns(3)
        c1.metric("Prix XRP", f"{price} USDC")
        c2.metric("Solde XRP", f"{xrp:.2f}")
        c3.metric("Solde USDC", f"{usdc:.2f}")

        # --- LOGIQUE BOULE DE NEIGE (DCA) ---
        # Si le prix baisse de 2%, le bot pourrait acheter ici
        # Si le prix monte de 3%, le bot pourrait vendre ici
        
        st.info(f"Dernière analyse : {time.strftime('%H:%M:%S')}")
        
        # Pause de 30 secondes avant de relancer tout seul
        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur réseau : {e}")
        time.sleep(10)
        st.rerun()
else:
    st.warning("❌ LE BOT EST À L'ARRÊT.")
    st.info("Clique sur DÉMARRER pour lancer l'automate.")
