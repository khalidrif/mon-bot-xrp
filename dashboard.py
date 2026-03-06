import streamlit as st
import krakenex

st.title("🎮 Centre de Commande Kraken")

# 1. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 2. Récupérer le prix actuel pour aider à choisir
res = k.query_public('Ticker', {'pair': 'XRPUSDC'})
prix_reel = float(res['result']['XRPUSDC']['c'][0])
st.metric("Prix XRP actuel", f"{prix_reel} USDC")

# 3. Formulaire de saisie pour tes Bots
st.write("### 🤖 Lancer une nouvelle Grille")
with st.form("grid_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        prix_achat = st.number_input("Prix d'Achat (USDC)", value=prix_reel, step=0.01)
    with col2:
        prix_vente = st.number_input("Prix de Vente (USDC)", value=prix_reel*1.02, step=0.01)
    with col3:
        quantite = st.number_input("Quantité de XRP", value=15.0, step=1.0)
    
    submit = st.form_submit_button("🚀 LANCER LE BOT")

# 4. Action au clic
if submit:
    try:
        # Placement de l'achat (Limit à ton prix choisi)
        buy = k.query_private('AddOrder', {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
            'price': str(prix_achat), 'volume': str(quantite)
        })
        # Placement de la vente
        sell = k.query_private('AddOrder', {
            'pair': 'XRPUSDC', 'type': 'sell', 'ordertype': 'limit',
            'price': str(prix_vente), 'volume': str(quantite)
        })
        st.success(f"✅ Bot lancé ! Achat à {prix_achat} / Vente à {prix_vente}")
        st.json(buy)
    except Exception as e:
        st.error(f"Erreur : {e}")

# 5. Afficher tes bots actifs
st.write("### 📊 Mes ordres en cours")
orders = k.query_private('OpenOrders')['result']['open']
if orders:
    st.write(orders)
else:
    st.info("Aucun bot actif.")
