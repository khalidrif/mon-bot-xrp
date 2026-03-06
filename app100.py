import streamlit as st
import ccxt

st.title("🔍 Diagnostic de ton Portefeuille")

@st.cache_resource
def init_k():
    return ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
    })

k = init_k()

try:
    bal = k.fetch_balance()
    
    st.write("### 📝 Voici ce que le bot voit réellement :")
    
    # On affiche TOUT ce qui n'est pas à zéro
    found = False
    for currency, amount in bal['total'].items():
        if amount > 0:
            st.success(f"✅ {currency} : **{amount}**")
            found = True
            
    if not found:
        st.error("❌ Le bot ne voit AUCUNE monnaie. Vérifie que ta clé API a bien la case 'Query Funds' cochée sur Kraken.")

except Exception as e:
    st.error(f"❌ Erreur technique : {e}")
