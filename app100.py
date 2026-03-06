import streamlit as st
import ccxt
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP BOT - BLOC 1", layout="centered")

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

st.title("🏓 Bloc 1 : Surveillance")

# --- TEST LECTURE ---
try:
    ticker = k.fetch_ticker('XRP/USDC')
    px = ticker['last']
    bal = k.fetch_balance()
    usdc = bal['free'].get('USDC', 0.0)
    xrp = bal['free'].get('XRP', 0.0)
    
    c1, c2 = st.columns(2)
    c1.metric("PRIX XRP", f"{px:.4f}$")
    c2.metric("SOLDE USDC", f"{usdc:.2f}$")
    
    st.write(f"🪙 XRP disponible : **{xrp:.2f}**")
    
    if st.button("🔄 Rafraîchir"):
        st.rerun()

except Exception as e:
    st.error(f"Erreur de lecture : {e}")

st.info("Si le prix et le solde (71.35$) s'affichent, le Bloc 1 est validé !")
