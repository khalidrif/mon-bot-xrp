# 1. LES IMPORTS (Toujours en premier !)
import streamlit as st
import pandas as pd
import ccxt
import datetime
import time
from config import get_kraken_connection

# 2. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Kraken Terminal Pro", layout="wide", page_icon="📈")

# Connexion via ton fichier config.py
try:
    kraken = get_kraken_connection()
except Exception as e:
    st.error(f"Erreur de configuration : {e}")
    st.stop()

st.title("🤖 Mon Terminal de Trading Kraken")

# Zone dynamique qui s'efface et se réécrit (Placeholder)
placeholder = st.empty()

# --- SECTION 3 : FORMULAIRES DE TRADING (Fixes) ---
st.divider()
col_achat, col_vente = st.columns(2)

# --- FORMULAIRE D'ACHAT ---
with col_achat:
    st.subheader("🛒 ACHETER du XRP")
    with st.form("buy_form"):
        p_achat = st.number_input("Prix d'achat cible ($)", step=0.0001, format="%.4f")
        budget_usdc = st.number_input("Budget USDC", min_value=10.0, value=25.0)
        if st.form_submit_button("🚀 PLACER ACHAT LIMIT"):
            try:
                qty = budget_usdc / p_achat
                res = kraken.create_order('XRP/USDC', 'limit', 'buy', qty, p_achat, {'validate': False})
                st.success(f"Ordre d'achat placé ! ID: {res['id']}")
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- FORMULAIRE DE VENTE ---
with col_vente:
    st.subheader("🔴 VENDRE du XRP")
    with st.form("sell_form"):
        p_vente = st.number_input("Prix de vente cible ($)", step=0.0001, format="%.4f")
        quantite_xrp = st.number_input("Nombre de XRP à vendre", min_value=5.0, value=10.0)
        if st.form_submit_button("🔥 PLACER VENTE LIMIT"):
            try:
                res_v = kraken.create_order('XRP/USDC', 'limit', 'sell', quantite_xrp, p_vente, {'validate': False})
                st.success(f"Ordre de vente placé ! ID: {res_v['id']}")
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- SECTION 4 : BOUCLE DE MISE À JOUR (Temps Réel) ---
while True:
    try:
        # Récupération des prix frais (Order Book)
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        prix_ask = ob['asks'][0][0]
        prix_bid = ob['bids'][0][0]
        prix_moyen = (prix_ask + prix_bid) / 2

        # Récupération du solde
        balance = kraken.fetch_balance()
        usdc = balance.get('USDC', {}).get('total', 0)
        xrp = balance.get('XRP', {}).get('total', 0)

        with placeholder.container():
            st.write(f"⏱️ Dernière mise à jour : **{datetime.datetime.now().strftime('%H:%M:%S')}**")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Portefeuille USDC", f"{usdc:,.2f} $")
            c2.metric("🪙 Stock XRP", f"{xrp:,.2f} XRP", f"{xrp * prix_moyen:,.2f} $")
            c3.metric("📈 Prix XRP/USDC", f"{prix_moyen:.4f} $")
            
            st.caption(f"Prix d'achat direct (Ask): {prix_ask}$ | Prix de vente direct (Bid): {prix_bid}$")
            
            # Tableau des actifs
            st.subheader("📝 Détail de mes avoirs")
            df_balance = pd.DataFrame(balance['total'].items(), columns=['Actif', 'Quantité'])
            df_nonzero = df_balance[df_balance['Quantité'] > 0].reset_index(drop=True)
            st.dataframe(df_nonzero, width='stretch')

    except Exception as e:
        st.error(f"Erreur de flux : {e}")
    
    # Pause de 5 secondes avant la prochaine lecture
    time.sleep(5)
