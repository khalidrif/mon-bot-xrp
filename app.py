import streamlit as st
import ccxt

st.title("🤖 Bot XRP Achat & Vente Rapide")

# Connexion Kraken
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    st.sidebar.success("Connecté à Kraken")
except Exception as e:
    st.sidebar.error(f"Erreur : {e}")
    st.stop()

# Formulaire de configuration
st.subheader("⚙️ Paramètres du Bot")

col1, col2, col3 = st.columns(3)
with col1:
    prix_achat = st.number_input("Prix d'ACHAT (USDC)", value=2.4000, format="%.4f")
with col2:
    prix_vente = st.number_input("Prix de VENTE (USDC)", value=2.6000, format="%.4f")
with col3:
    montant_xrp = st.number_input("Montant (XRP)", value=20.0, step=1.0)

# Bouton de lancement
if st.button("🚀 Lancer le Bot (Placer les 2 ordres)"):
    try:
        # 1. Placer l'achat
        achat = exchange.create_limit_buy_order('XRP/USDC', montant_xrp, prix_achat)
        st.success(f"✅ Ordre d'ACHAT placé à {prix_achat}")
        
        # 2. Placer la vente
        vente = exchange.create_limit_sell_order('XRP/USDC', montant_xrp, prix_vente)
        st.success(f"✅ Ordre de VENTE placé à {prix_vente}")
        
        st.balloons()
    except Exception as e:
        st.error(f"Erreur Kraken : {e}")

# Affichage des ordres en cours
st.divider()
st.subheader("📋 Ordres actifs sur Kraken")
if st.button("Actualiser la liste"):
    orders = exchange.fetch_open_orders('XRP/USDC')
    if orders:
        for o in orders:
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"**{o['side'].upper()}** : {o['amount']} XRP @ {o['price']} USDC")
            if col_b.button("Annuler", key=o['id']):
                exchange.cancel_order(o['id'], 'XRP/USDC')
                st.rerun()
    else:
        st.info("Aucun ordre actif.")
