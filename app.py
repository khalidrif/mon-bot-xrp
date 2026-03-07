import streamlit as st
import ccxt

st.title("XRP Bot Individuel - Kraken 🐙")

# Connexion à Kraken
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    st.sidebar.success("Connecté à Kraken")
except Exception as e:
    st.sidebar.error(f"Erreur Kraken : {e}")
    st.stop()

# Paramètres de l'ordre
symbol = 'XRP/USD' # Ou 'XRP/EUR' ou 'XRP/USDT' selon votre solde
st.sidebar.header("Réglages du Bot")
type_ordre = st.sidebar.selectbox("Action", ["ACHAT", "VENTE"])
prix_cible = st.sidebar.number_input("Prix (USD)", value=0.6000, format="%.4f")
quantite = st.sidebar.number_input("Quantité XRP", value=30.0)

# Bouton pour lancer CE bot spécifique
if st.button(f"Lancer ce Bot {type_ordre}"):
    try:
        if type_ordre == "ACHAT":
            ordre = exchange.create_limit_buy_order(symbol, quantite, prix_cible)
        else:
            ordre = exchange.create_limit_sell_order(symbol, quantite, prix_cible)
        
        st.success(f"✅ Bot ajouté ! ID Kraken : {ordre['id']}")
    except Exception as e:
        st.error(f"Erreur lors du placement : {e}")

# Gestion des bots actifs
st.divider()
st.subheader("Mes Bots Actifs sur Kraken")

if st.button("Actualiser la liste"):
    try:
        open_orders = exchange.fetch_open_orders(symbol)
        if open_orders:
            for o in open_orders:
                col1, col2 = st.columns([3, 1])
                col1.info(f"Type: {o['side'].upper()} | Prix: {o['price']} | Qté: {o['amount']}")
                if col2.button("Annuler", key=o['id']):
                    exchange.cancel_order(o['id'], symbol)
                    st.rerun()
        else:
            st.write("Aucun bot actif.")
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
