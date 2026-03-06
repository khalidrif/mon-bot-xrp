import streamlit as st
import krakenex
import pandas as pd
import plotly.graph_objects as go
import os

# Connexion API (Utilise tes secrets GitHub/Streamlit)
k = krakenex.API(key=os.getenv('KRAKEN_KEY'), secret=os.getenv('KRAKEN_SECRET'))

st.title("📈 Dashboard Kraken Grid Bot")

# 1. Récupérer les données
res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])

res_orders = k.query_private('OpenOrders')
orders = res_orders['result']['open']

# 2. Affichage du prix
st.metric("Prix actuel XRP", f"{prix_actuel} USDC")

# 3. Création du Graphique
fig = go.Figure()

# Ligne du prix actuel
fig.add_hline(y=prix_actuel, line_dash="dot", line_color="white", annotation_text="Prix Actuel")

# Ajouter les ordres de vente ouverts sur le graphique
if orders:
    for oid, details in orders.items():
        prix_ordre = float(details['descr']['price'])
        type_ordre = details['descr']['type']
        color = "red" if type_ordre == "sell" else "green"
        
        fig.add_hline(y=prix_ordre, line_color=color, annotation_text=f"Ordre {type_ordre}")

fig.update_layout(title="Ma Grille sur Kraken", yaxis_title="Prix USDC")
st.plotly_chart(fig)

# 4. Tableau des ordres
if orders:
    st.write("### Ordres en attente")
    st.write(orders)
else:
    st.info("Aucun ordre ouvert. Le bot attend le prochain cycle.")
