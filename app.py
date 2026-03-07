import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Kraken XRP Buy", page_icon="💳")
st.title("💳 Achat Immédiat XRP sur Kraken")

# 1. Connexion avec correction Nonce
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: int(time.time() * 1000)}
    })

exchange = get_exchange()

# 2. Vérification Solde
try:
    balance = exchange.fetch_balance()
    usdc_dispo = balance.get('USDC', {}).get('free', 0)
    st.sidebar.metric("Ton Solde USDC", f"{usdc_dispo:.2f}")
except Exception as e:
    st.sidebar.error(f"Erreur API : {e}")

# 3. Paramètres d'achat
st.subheader("Configuration de l'ordre")
montant_xrp = st.number_input("Quantité de XRP à acheter", value=20.0, min_value=10.0, step=1.0)

# 4. Action d'achat
if st.button("🚀 ENVOYER L'ORDRE D'ACHAT MAINTENANT"):
    status = st.empty()
    try:
        status.info(f"⏳ Envoi de l'ordre au marché pour {montant_xrp} XRP...")
        
        # --- L'ORDRE REEL ---
        ordre = exchange.create_market_buy_order('XRP/USDC', montant_xrp)
        # --------------------
        
        st.success("✅ ORDRE ACCEPTÉ PAR KRAKEN !")
        st.json(ordre) # Affiche les détails de la transaction (ID, prix moyen, etc.)
        st.balloons()
        
    except ccxt.InsufficientFunds:
        st.error("❌ Erreur : Tu n'as pas assez de USDC (pense aux frais de ~0.26%).")
    except Exception as e:
        st.error(f"❌ L'ordre a échoué : {e}")

st.divider()
st.caption("Note : Ce bouton achète du XRP au prix actuel du marché (Market Order).")
