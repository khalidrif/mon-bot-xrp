import streamlit as st
import ccxt
import pandas as pd
import time

# 1. Configuration de l'interface
st.set_page_config(page_title="XRP Snowball Bot", page_icon="❄️", layout="wide")
st.title("❄️ Bot Grid XRP - Stratégie Boule de Neige")

# 2. Connexion sécurisée à Kraken
@st.cache_resource
def init_exchange():
    try:
        return ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_API_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
        })
    except Exception as e:
        st.error(f"Erreur de connexion API : {e}")
        return None

exchange = init_exchange()

if exchange:
    # 3. Paramètres via Sidebar
    st.sidebar.header("⚙️ Paramètres")
    pair = st.sidebar.selectbox("Paire", ["XRP/USD", "XRP/EUR", "XRP/USDT"], index=0)
    grid_levels = st.sidebar.slider("Nombre de paliers", 5, 20, 10)
    risk_pct = st.sidebar.slider("Risque par palier (%)", 1.0, 10.0, 3.0) / 100
    range_pct = st.sidebar.slider("Largeur de grille (+/- %)", 1.0, 15.0, 5.0) / 100

    # 4. Récupération des données en direct
    try:
        ticker = exchange.fetch_ticker(pair)
        current_price = ticker['last']
        balance = exchange.fetch_balance()
        
        # Extraction dynamique des soldes
        fiat_cur = pair.split('/')[1]
        fiat_bal = balance['total'].get(fiat_cur, 0.0)
        xrp_bal = balance['total'].get('XRP', 0.0)

        # Affichage
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Prix {pair}", f"{current_price:.4f} {fiat_cur}")
        c2.metric(f"Solde {fiat_cur}", f"{fiat_bal:.2f}")
        c3.metric("Solde XRP", f"{xrp_bal:.2f}")

        # 5. Calcul de la Grille "Boule de Neige"
        # La quantité s'adapte au solde disponible (Intérêt composé)
        amount_per_level = (fiat_bal * risk_pct) / current_price
        
        lower_price = current_price * (1 - range_pct)
        upper_price = current_price * (1 + range_pct)
        step = (upper_price - lower_price) / grid_levels

        st.subheader("📋 Liste des ordres à placer")
        grid_df = []
        for i in range(grid_levels + 1):
            price = round(lower_price + (i * step), 4)
            side = "sell" if price > current_price else "buy"
            grid_df.append({"Price": price, "Side": side, "Amount": round(amount_per_level, 2)})
        
        st.table(pd.DataFrame(grid_df))

        # 6. BOUTON D'ACTION (REEL)
        if st.button("🚀 LANCER LES ORDRES SUR KRAKEN"):
            st.warning("🔄 Connexion à Kraken... Placement des ordres.")
            for order in grid_df:
                try:
                    if order["Side"] == "buy":
                        exchange.create_limit_buy_order(pair, order["Amount"], order["Price"])
                    else:
                        exchange.create_limit_sell_order(pair, order["Amount"], order["Price"])
                    st.success(f"Ordre {order['Side']} placé à {order['Price']}")
                except Exception as e:
                    st.error(f"Erreur sur le prix {order['Price']}: {e}")
            st.balloons()

    except Exception as e:
        st.error(f"Erreur de chargement des données : {e}")

# Rafraîchissement auto
if st.sidebar.checkbox("Activer l'auto-refresh (30s)"):
    time.sleep(30)
    st.rerun()
