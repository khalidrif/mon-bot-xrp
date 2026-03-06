import streamlit as st
import ccxt
import pandas as pd

# 1. Config Page
st.set_page_config(page_title="XRP Snowball Bot", page_icon="❄️")
st.title("❄️ XRP Snowball Grid Bot")

# 2. Connexion Kraken via Secrets
@st.cache_resource
def init_kraken():
    return ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })

try:
    kraken = init_kraken()
    
    # 3. Sidebar - Paramètres de la stratégie
    st.sidebar.header("Configuration de la Grille")
    pair = st.sidebar.selectbox("Paire de trading", ["XRP/USD", "XRP/EUR", "XRP/USDT"])
    grid_levels = st.sidebar.slider("Nombre de niveaux (Grille)", 5, 20, 10)
    amount_per_level = st.sidebar.number_input("Quantité XRP par niveau", min_value=10.0, value=20.0)
    range_pct = st.sidebar.slider("Écart de prix (%)", 1.0, 10.0, 5.0) / 100

    # 4. Données en temps réel
    ticker = kraken.fetch_ticker(pair)
    current_price = ticker['last']
    
    col1, col2 = st.columns(2)
    col1.metric(f"Prix {pair}", f"{current_price:.4f}")
    
    # 5. Logique de la Grille (Visualisation)
    lower_price = current_price * (1 - range_pct)
    upper_price = current_price * (1 + range_pct)
    
    st.subheader("Visualisation de la Stratégie")
    st.write(f"Le bot achètera entre **{lower_price:.4f}** et vendra jusqu'à **{upper_price:.4f}**.")

    # 6. Bouton d'action
    if st.button("Lancer la Grille sur Kraken"):
        st.warning("⚠️ Action réelle : Le bot va placer des ordres limités.")
        
        step = (upper_price - lower_price) / grid_levels
        for i in range(grid_levels + 1):
            target_price = lower_price + (i * step)
            try:
                if target_price < current_price:
                    # kraken.create_limit_buy_order(pair, amount_per_level, target_price)
                    st.write(f"✅ Ordre d'ACHAT préparé à {target_price:.4f}")
                elif target_price > current_price:
                    # kraken.create_limit_sell_order(pair, amount_per_level, target_price)
                    st.write(f"✅ Ordre de VENTE préparé à {target_price:.4f}")
            except Exception as e:
                st.error(f"Erreur sur le niveau {target_price}: {e}")

except Exception as e:
    st.error(f"Impossible de se connecter à Kraken : {e}")
    st.info("Vérifie tes secrets dans .streamlit/secrets.toml")

