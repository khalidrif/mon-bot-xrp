import streamlit as st
import ccxt
import time
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Multi-Grid", layout="wide")
st.title("🧱 Bot XRP/USDC - Multi-Fourchettes (Grid)")

# Connexion Kraken
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    symbol = "XRP/USDC"
except:
    st.error("Erreur API Kraken.")
    st.stop()

# --- RÉGLAGES (Sidebar) ---
with st.sidebar:
    st.header("📊 Configuration de la Grille")
    nb_paliers = st.slider("Nombre de paliers", 1, 5, 3)
    intervalle = st.number_input("Écart entre paliers (USDC)", value=0.02, format="%.4f")
    mise_par_palier = st.number_input("Mise par palier (USDC)", min_value=15.0, value=20.0)
    profit_par_palier = st.number_input("Profit cible par palier (USDC)", value=0.03, format="%.4f")

# --- MÉMOIRE ---
if 'actif' not in st.session_state: st.session_state.actif = False
if 'prix_base' not in st.session_state:
    st.session_state.prix_base = exchange.fetch_ticker(symbol)['last']

# --- CONTRÔLES ---
c1, c2 = st.columns(2)
if c1.button("🚀 DÉMARRER LA GRILLE", type="primary", use_container_width=True):
    st.session_state.actif = True
if c2.button("🛑 ARRÊTER", use_container_width=True):
    st.session_state.actif = False

st.divider()

# --- BOUCLE DE TRADING ---
if st.session_state.actif:
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        bal = exchange.fetch_balance()
        xrp_bal = bal['free'].get('XRP', 0.0)
        usdc_bal = bal['free'].get('USDC', 0.0)

        # 1. GÉNÉRATION DES FOURCHETTES
        paliers = []
        for i in range(1, nb_paliers + 1):
            p_achat = st.session_state.prix_base - (i * intervalle)
            p_vente = p_achat + profit_par_palier
            paliers.append({"Niveau": i, "Achat": p_achat, "Vente": p_vente})
        
        df_paliers = pd.DataFrame(paliers)

        # 2. AFFICHAGE
        st.subheader(f"📈 Prix Actuel : {price:.4f} USDC")
        st.table(df_paliers)
        st.write(f"💰 **Solde :** {usdc_bal:.2f} USDC | {xrp_bal:.2f} XRP")

        # 3. LOGIQUE D'EXÉCUTION (Boucle sur les paliers)
        for p in paliers:
            # ACHAT : Si le prix descend sous un palier d'achat
            if price <= p['Achat'] and usdc_bal >= mise_par_palier:
                st.warning(f"🛒 Achat Palier {p['Niveau']} à {price}")
                qty = float(exchange.amount_to_precision(symbol, mise_par_palier / price))
                exchange.create_market_buy_order(symbol, qty)
                time.sleep(5)
                st.rerun()

            # VENTE : Si le prix remonte au prix de vente du palier
            # Note : On vend si on a du stock et que le prix dépasse la cible de vente
            if price >= p['Vente'] and xrp_bal > 10:
                st.success(f"💰 Vente Profit Palier {p['Niveau']} à {price}")
                qty_sell = float(exchange.amount_to_precision(symbol, xrp_bal))
                exchange.create_market_sell_order(symbol, qty_sell)
                time.sleep(5)
                st.rerun()

        # Rafraîchissement
        st.info(f"Dernière analyse : {time.strftime('%H:%M:%S')}")
        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"Erreur : {e}")
        time.sleep(20)
        st.rerun()
else:
    st.info("Bot à l'arrêt. Configurez vos paliers à gauche.")
