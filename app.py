import streamlit as st
import ccxt

st.title("XRP Single Bot Manager 🤖")

# Connexion via Secrets Streamlit
try:
    exchange = ccxt.binance({
        'apiKey': st.secrets["BINANCE_API_KEY"],
        'secret': st.secrets["BINANCE_SECRET"],
        'enableRateLimit': True,
    })
    st.success("Connecté à l'Exchange")
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# Configuration de l'ordre individuel
st.sidebar.header("Paramètres du Bot")
type_ordre = st.sidebar.selectbox("Type de Bot", ["ACHAT (Limit Buy)", "VENTE (Limit Sell)"])
prix_cible = st.sidebar.number_input("Prix cible (USDT)", value=0.600, format="%.4f")
quantite = st.sidebar.number_input("Quantité XRP", value=20.0)

if st.button(f"Lancer le Bot {type_ordre}"):
    try:
        if "ACHAT" in type_ordre:
            ordre = exchange.create_limit_buy_order('XRP/USDT', quantite, prix_cible)
        else:
            ordre = exchange.create_limit_sell_order('XRP/USDT', quantite, prix_cible)
        
        st.balloons()
        st.success(f"Bot activé ! ID de l'ordre : {ordre['id']}")
        st.write(f"Détails : {quantite} XRP à {prix_cible} USDT")
        
    except Exception as e:
        st.error(f"Impossible de lancer le bot : {e}")

# Affichage des bots (ordres) actifs
st.divider()
st.subheader("Mes Bots en cours")
if st.button("Actualiser la liste"):
    open_orders = exchange.fetch_open_orders('XRP/USDT')
    if open_orders:
        for o in open_orders:
            st.info(f"ID: {o['id']} | {o['side'].upper()} | Prix: {o['price']} | Qté: {o['amount']}")
    else:
        st.write("Aucun bot actif pour le moment.")
