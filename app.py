import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Test Bot XRP", layout="centered")
st.title("🧪 Test d'Achat/Vente (Simulation)")

# 1. CONNEXION (via Secrets)
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True
    })
    st.success("✅ Connecté à Kraken")
except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")
    st.stop()

# 2. RÉCUPÉRATION DES INFOS
symbol = "XRP/USDC"
try:
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['last']
    bal = exchange.fetch_balance()
    usdc = bal['free'].get('USDC', 0.0)
    xrp = bal['free'].get('XRP', 0.0)
    
    st.write(f"**Prix actuel :** {price} USDC")
    st.write(f"**Ton solde :** {usdc:.2f} USDC / {xrp:.2f} XRP")
except Exception as e:
    st.error(f"Impossible de lire le marché : {e}")

st.divider()

# 3. BOUTONS DE TEST
st.subheader("Simuler un ordre (Validation seule)")
st.info("Ces boutons envoient l'ordre avec 'validate: True'. Aucun argent ne sera dépensé.")

col1, col2 = st.columns(2)

# TEST ACHAT
if col1.button("🛒 Tester un ACHAT (20 USDC)"):
    try:
        # Calcul quantité
        qty = 20 / price
        # L'option 'validate': True empêche l'exécution réelle
        res = exchange.create_market_buy_order(symbol, qty, params={'validate': True})
        st.success("✅ Test ACHAT réussi ! Kraken a validé l'ordre.")
        st.json(res)
    except Exception as e:
        st.error(f"❌ Échec du test achat : {e}")

# TEST VENTE
if col2.button("💰 Tester une VENTE (Toute la balance)"):
    try:
        if xrp > 5:
            res = exchange.create_market_sell_order(symbol, xrp, params={'validate': True})
            st.success("✅ Test VENTE réussi ! Kraken a validé l'ordre.")
            st.json(res)
        else:
            st.warning("Solde XRP insuffisant pour tester la vente (min ~5 XRP).")
    except Exception as e:
        st.error(f"❌ Échec du test vente : {e}")

st.divider()
st.caption("Si tu reçois un message 'Success' ou un bloc de texte (JSON), cela veut dire que ton bot est prêt pour le trading réel.")
