import streamlit as st
import ccxt

# --- 1. CONNEXION ---
st.set_page_config(page_title="XRP BOT - BLOC 2", layout="centered")

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

st.title("🛒 Bloc 2 : Test d'Achat")

# --- 2. RÉCUPÉRATION DES INFOS ---
try:
    ticker = k.fetch_ticker('XRP/USDC')
    px_live = ticker['last']
    bal = k.fetch_balance()
    usdc_dispo = bal['free'].get('USDC', 0.0)
    
    st.write(f"Prix actuel : **{px_live:.4f} $**")
    st.write(f"Ton USDC disponible : **{usdc_dispo:.2f} $**")
    st.divider()

    # --- 3. COMMANDE DE TEST ---
    p_achat = st.number_input("À quel prix veux-tu acheter ?", value=px_live, format="%.4f")
    
    if st.button("🚀 PLACER L'ORDRE D'ACHAT (ALL-IN)", type="primary", use_container_width=True):
        if usdc_dispo > 5:
            # Calcul du volume max
            vol = float(k.amount_to_precision('XRP/USDC', usdc_dispo / p_achat))
            
            # Tentative de placement
            res = k.create_limit_buy_order('XRP/USDC', vol, p_achat, {'post-only': True})
            st.success(f"✅ ORDRE PLACÉ ! ID: {res['id']}")
            st.info(f"Volume : {vol} XRP à {p_achat} $")
        else:
            st.error("Solde USDC insuffisant (Min 5$)")

except Exception as e:
    st.error(f"Erreur : {e}")

if st.button("🗑️ ANNULER TOUS LES ORDRES (SÉCURITÉ)"):
    k.cancel_all_orders('XRP/USDC')
    st.warning("Tous les ordres XRP ont été annulés.")
