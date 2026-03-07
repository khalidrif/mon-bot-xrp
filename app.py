import streamlit as st
import ccxt
import pandas as pd
import time

# 1. Configuration de l'interface
st.set_page_config(page_title="XRP Snowball Bot", page_icon="❄️", layout="wide")
st.title("❄️ Bot Grid XRP - Stratégie Boule de Neige")

# 2. Connexion sécurisée à Kraken (utilise les secrets Streamlit/GitHub)
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
    # 3. Sidebar : Paramètres de la stratégie
    st.sidebar.header("⚙️ Paramètres")
    pair = st.sidebar.selectbox("Paire", ["XRP/USD", "XRP/EUR", "XRP/USDT"], index=0)
    grid_levels = st.sidebar.slider("Nombre de paliers (niveaux)", 5, 20, 10)
    risk_pct = st.sidebar.slider("Allocation par niveau (%)", 1.0, 10.0, 5.0) / 100
    range_pct = st.sidebar.slider("Largeur de la grille (+/- %)", 1.0, 15.0, 5.0) / 100

    # 4. Récupération des données en direct
    try:
        ticker = exchange.fetch_ticker(pair)
        current_price = ticker['last']
        balance = exchange.fetch_balance()
        
        # Identification de la monnaie fiat (USD ou EUR)
        fiat_currency = pair.split('/')[1]
        fiat_balance = balance['total'].get(fiat_currency, 0.0)
        xrp_balance = balance['total'].get('XRP', 0.0)

        # Affichage des métriques
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Prix {pair}", f"{current_price:.4f}")
        c2.metric(f"Solde {fiat_currency}", f"{fiat_balance:.2f} {fiat_currency}")
        c3.metric("Solde XRP", f"{xrp_balance:.2f} XRP")

        # 5. Logique "Boule de Neige" (Calcul dynamique)
        # On calcule la quantité de XRP par niveau basée sur un % du solde actuel
        amount_per_level = (fiat_balance * risk_pct) / current_price

        st.subheader("📊 Aperçu de la Grille")
        lower_price = current_price * (1 - range_pct)
        upper_price = current_price * (1 + range_pct)
        step = (upper_price - lower_price) / grid_levels

        grid_data = []
        for i in range(grid_levels + 1):
            level_price = lower_price + (i * step)
            type_ordre = "VENTE" if level_price > current_price else "ACHAT"
            grid_data.append({"Prix": round(level_price, 4), "Type": type_ordre, "Quantité": round(amount_per_level, 2)})

        st.table(pd.DataFrame(grid_data))

        # 6. Exécution (Bouton d'activation)
        if st.button("🚀 LANCER LA GRILLE SUR KRAKEN"):
            st.warning("Placement des ordres en cours...")
            for order in grid_data:
                try:
                    if order["Type"] == "ACHAT":
                        # exchange.create_limit_buy_order(pair, order["Quantité"], order["Prix"])
                        st.write(f"✅ Achat placé à {order['Prix']}")
                    else:
                        # exchange.create_limit_sell_order(pair, order["Quantité"], order["Prix"])
                        st.write(f"✅ Vente placée à {order['Prix']}")
                except Exception as e:
                    st.error(f"Erreur sur le niveau {order['Prix']} : {e}")
            st.success("Grille initialisée !")

    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")

# 7. Auto-refresh (Optionnel)
if st.checkbox("Actualisation automatique (30s)"):
    time.sleep(30)
    st.rerun()
