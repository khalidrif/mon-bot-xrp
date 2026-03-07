import streamlit as st
import ccxt
import pandas as pd
import time

# Interface utilisateur
st.set_page_config(page_title="XRP Grid Bot", page_icon="📈")
st.title("🚀 XRP Grid Bot (4 Niveaux)")

# Connexion sécurisée à l'exchange (ex: Binance)
try:
    exchange = ccxt.binance({
        'apiKey': st.secrets["BINANCE_API_KEY"],
        'secret': st.secrets["BINANCE_SECRET"],
        'enableRateLimit': True,
    })
    st.sidebar.success("✅ Connecté à l'Exchange")
except Exception as e:
    st.sidebar.error(f"❌ Erreur : {e}")
    st.info("Ajoutez vos clés dans les 'Secrets' de Streamlit.")
    st.stop()

# Paramètres configurables
symbol = 'XRP/USDT'
st.sidebar.header("Configuration")
amount = st.sidebar.number_input("Quantité XRP par ordre", value=20.0, step=1.0)
grid_gap = st.sidebar.number_input("Écart entre ordres (USDT)", value=0.01, format="%.3f")

if st.button("Initialiser la Grille (4 ordres)"):
    try:
        # Annulation des anciens ordres
        st.write("Nettoyage des ordres en cours...")
        exchange.cancel_all_orders(symbol)
        
        # Récupération du prix actuel
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        st.metric("Prix XRP actuel", f"{current_price} USDT")

        placed_orders = []

        # Placement des 2 ordres d'achat (Buy) sous le prix
        for i in range(1, 3):
            price = current_price - (i * grid_gap)
            order = exchange.create_limit_buy_order(symbol, amount, price)
            placed_orders.append({'ID': order['id'], 'Type': 'ACHAT', 'Prix': price})

        # Placement des 2 ordres de vente (Sell) au-dessus du prix
        for i in range(1, 3):
            price = current_price + (i * grid_gap)
            order = exchange.create_limit_sell_order(symbol, amount, price)
            placed_orders.append({'ID': order['id'], 'Type': 'VENTE', 'Prix': price})

        st.success("Grille de 4 ordres déployée !")
        st.table(pd.DataFrame(placed_orders))

    except Exception as e:
        st.error(f"Erreur technique : {e}")

# Monitoring simple
st.divider()
if st.checkbox("Surveiller les ordres actifs"):
    placeholder = st.empty()
    while True:
        try:
            open_orders = exchange.fetch_open_orders(symbol)
            placeholder.write(f"Nombre d'ordres en attente : {len(open_orders)}")
            time.sleep(15) # Pause pour éviter le spam d'API
        except:
            break
