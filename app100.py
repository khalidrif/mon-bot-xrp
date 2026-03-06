import streamlit as st
import ccxt

st.set_page_config(page_title="XRP CANCEL TEST", layout="centered")

@st.cache_resource
def init_k():
    ex = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    ex.nonce = lambda: ex.milliseconds()
    return ex

k = init_k()

st.title("🗑️ Test d'Annulation Kraken")

# Affichage des ordres ouverts pour voir celui de 0.50$
try:
    orders = k.fetch_open_orders('XRP/USDC')
    if orders:
        st.write("### Ordre(s) trouvé(s) :")
        for o in orders:
            st.code(f"ID: {o['id']} | {o['side']} | {o['amount']} XRP à {o['price']}$")
        
        if st.button("🗑️ FORCE ANNULATION DE TOUT", type="primary", use_container_width=True):
            try:
                # On utilise la commande globale pour être sûr à 100%
                k.cancel_all_orders('XRP/USDC')
                st.success("✅ TOUT A ÉTÉ ANNULÉ ! Vérifie ton compte Kraken, l'ordre à 0.50$ doit avoir disparu.")
            except Exception as e:
                st.error(f"❌ Erreur lors de l'annulation : {e}")
    else:
        st.info("Aucun ordre ouvert trouvé sur XRP/USDC. (L'ordre a peut-être déjà été annulé ou n'existe plus)")

except Exception as e:
    st.error(f"Erreur de lecture : {e}")

if st.button("🔄 Rafraîchir la liste"):
    st.rerun()
