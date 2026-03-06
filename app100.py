import streamlit as st
import ccxt
import time

# --- 1. INITIALISATION ---
st.set_page_config(page_title="XRP TEST MODE", layout="centered")

@st.cache_resource
def init_k():
    try:
        ex = ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
        })
        ex.nonce = lambda: ex.milliseconds()
        return ex
    except Exception as e:
        st.error(f"❌ Erreur Configuration Secrets : {e}")
        return None

k = init_k()

# --- 2. MÉMOIRE DU TEST ---
if 'test' not in st.session_state:
    st.session_state.test = {"step": 1, "log": "En attente..."}

st.title("🧪 Mode Test Kraken")

# --- 3. TEST ÉTAPE PAR ÉTAPE ---

# TEST 1 : LECTURE DU COMPTE
if st.button("🔍 TEST 1 : LIRE LE SOLDE"):
    try:
        bal = k.fetch_balance()
        usdc = bal['total'].get('USDC', 0)
        xrp = bal['total'].get('XRP', 0)
        st.success(f"✅ Connexion réussie !\nSolde : {usdc} USDC | {xrp} XRP")
        st.session_state.test["step"] = 2
    except Exception as e:
        st.error(f"❌ Échec de lecture : {e}\n(Vérifiez les permissions 'Query Funds' de votre clé API)")

# TEST 2 : ANNULATION (Si Test 1 OK)
if st.session_state.test["step"] >= 2:
    st.divider()
    if st.button("🧹 TEST 2 : NETTOYER KRAKEN"):
        try:
            k.cancel_all_orders('XRP/USDC')
            st.success("✅ Kraken a accepté l'ordre d'annulation.")
            st.session_state.test["step"] = 3
        except Exception as e:
            st.error(f"❌ Échec annulation : {e}\n(Vérifiez la permission 'Modify Orders')")

# TEST 3 : PLACEMENT ORDRE (Si Test 2 OK)
if st.session_state.test["step"] >= 3:
    st.divider()
    st.warning("⚠️ Ce test va placer un VRAI ordre d'achat à 0.50$ (très bas) pour tester l'écriture.")
    if st.button("📝 TEST 3 : PLACER ORDRE TEST"):
        try:
            # On place un achat à 0.50$ (pour être sûr qu'il ne soit pas exécuté)
            res = k.create_limit_buy_order('XRP/USDC', 10, 0.50)
            st.success(f"✅ ORDRE PLACÉ ! ID: {res['id']}")
            st.info("Allez voir sur votre appli Kraken, l'ordre à 0.50$ doit être présent.")
        except Exception as e:
            st.error(f"❌ Échec placement : {e}")

if st.button("🔄 RECOMMENCER LES TESTS"):
    st.session_state.test["step"] = 1
    st.rerun()
