import streamlit as st
import ccxt
import time

# --- 1. CONNEXION ---
st.set_page_config(page_title="RESET TOTAL", layout="centered")

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
    except: return None

k = init_k()

st.title("🧹 Grand Nettoyage")

# --- 2. ACTION DE RESET ---
if st.button("🚨 EFFACER TOUT ET REPARTIR À ZÉRO", use_container_width=True, type="primary"):
    # A. On vide la mémoire de l'iPhone/PC
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # B. On annule TOUS les ordres sur Kraken
    try:
        k.cancel_all_orders('XRP/USDC')
        st.success("✅ Kraken : Tous les ordres annulés.")
    except:
        st.warning("⚠️ Aucun ordre à annuler sur Kraken.")
    
    st.success("✅ Mémoire locale : Vidée.")
    st.info("Le bot est maintenant comme neuf (0 cycle, 0 profit).")
    st.balloons()
    time.sleep(2)
    st.rerun()

st.write("Cliquez sur le bouton pour remettre le bot à 0 cycle et 0 profit.")
