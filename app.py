import streamlit as st
import ccxt

# Configuration de la page
st.set_page_config(page_title="Kraken XRP Bot", page_icon="🐙")
st.title("🐙 Kraken Simple Bot (XRP/USDC)")

# Connexion sécurisée
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    st.sidebar.success("Connecté à Kraken")
except Exception as e:
    st.sidebar.error(f"Erreur de connexion : {e}")
    st.stop()

# 1. Configuration du bot individuel
st.subheader("➕ Configurer un nouveau Bot")

col1, col2, col3 = st.columns(3)
with col1:
    action = st.selectbox("Action", ["ACHAT", "VENTE"])
with col2:
    prix = st.number_input("Prix (USDC)", value=2.4000, format="%.4f")
with col3:
    quantite = st.number_input("Quantité (XRP)", value=20.0, step=1.0)

# Calcul rapide pour info
total = prix * quantite
st.caption(f"Total estimé : {total:.2f} USDC")

if st.button(f"Lancer ce Bot {action}"):
    try:
        if action == "ACHAT":
            ordre = exchange.create_limit_buy_order('XRP/USDC', quantite, prix)
        else:
            ordre = exchange.create_limit_sell_order('XRP/USDC', quantite, prix)
        
        st.success(f"✅ Bot {action} activé ! ID : {ordre['id']}")
    except Exception as e:
        st.error(f"Erreur Kraken : {e}")

# 2. Surveillance des bots actifs
st.divider()
st.subheader("📋 Mes Bots en attente")

if st.button("Actualiser la liste"):
    try:
        open_orders = exchange.fetch_open_orders('XRP/USDC')
        if not open_orders:
            st.info("Aucun bot actif pour le moment.")
        else:
            for o in open_orders:
                with st.container():
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.write(f"**{o['side'].upper()}**")
                    c2.write(f"{o['amount']} XRP @ {o['price']} USDC")
                    if c3.button("❌", key=o['id']):
                        exchange.cancel_order(o['id'], 'XRP/USDC')
                        st.rerun()
    except Exception as e:
        st.error(f"Erreur lecture : {e}")
