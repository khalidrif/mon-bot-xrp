import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Kraken Multi-Grid", layout="wide")
st.title("🤖 Gestionnaire de Bots XRP Indépendants")

# Connexion Kraken
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    st.sidebar.success("✅ Connecté à Kraken")
except Exception as e:
    st.sidebar.error(f"❌ Erreur : {e}")
    st.stop()

def monitor_cycle(label, p_buy, p_sell, qty, ui_element):
    """Gère la logique d'un bot sur une seule ligne d'affichage"""
    symbol = 'XRP/USDC'
    
    while st.session_state.running:
        # Étape 1 : ACHAT
        ui_element.info(f"**[{label}]** 📥 Placement Achat à **{p_buy}**...")
        try:
            order = exchange.create_limit_buy_order(symbol, qty, p_buy)
            while st.session_state.running:
                check = exchange.fetch_order(order['id'], symbol)
                if check['status'] == 'closed':
                    ui_element.success(f"**[{label}]** ✅ Acheté ! Préparation Vente...")
                    break
                time.sleep(10)
        except Exception as e:
            ui_element.error(f"Erreur {label}: {e}")
            break

        # Étape 2 : VENTE
        ui_element.warning(f"**[{label}]** 📤 Placement Vente à **{p_sell}**...")
        try:
            order = exchange.create_limit_sell_order(symbol, qty, p_sell)
            while st.session_state.running:
                check = exchange.fetch_order(order['id'], symbol)
                if check['status'] == 'closed':
                    ui_element.success(f"**[{label}]** 💰 Cycle terminé ! Redémarrage...")
                    break
                time.sleep(10)
        except Exception as e:
            ui_element.error(f"Erreur {label}: {e}")
            break

# --- INTERFACE DE CONFIGURATION ---
if 'running' not in st.session_state:
    st.session_state.running = False

st.write("### ⚙️ Configurer vos lignes (Bots)")

# Ligne 1 (Bot Haut)
c1, c2, c3 = st.columns(3)
with c1: p1_buy = st.number_input("Bot 1 : Achat", value=2.50, format="%.3f")
with c2: p1_sell = st.number_input("Bot 1 : Vente", value=2.60, format="%.3f")
with c3: qty1 = st.number_input("Bot 1 : Quantité", value=20.0, key="q1")

# Ligne 2 (Bot Bas)
c4, c5, c6 = st.columns(3)
with c4: p2_buy = st.number_input("Bot 2 : Achat", value=2.30, format="%.3f", key="b2")
with c5: p2_sell = st.number_input("Bot 2 : Vente", value=2.40, format="%.3f", key="s2")
with c6: qty2 = st.number_input("Bot 2 : Quantité", value=20.0, key="q2")

st.divider()

# --- ZONE DE SURVEILLANCE ---
st.write("### 📊 État des Bots en Temps Réel")
line1 = st.empty() # Emplacement réservé pour le Bot 1
line2 = st.empty() # Emplacement réservé pour le Bot 2

if not st.session_state.running:
    if st.button("▶️ DÉMARRER TOUS LES BOTS"):
        st.session_state.running = True
        # Note: Pour un vrai parallélisme H24, il faudrait utiliser du threading.
        # Ici, Streamlit exécutera les vérifications séquentiellement.
        while st.session_state.running:
            monitor_cycle("BOT HAUT", p1_buy, p1_sell, qty1, line1)
            monitor_cycle("BOT BAS", p2_buy, p2_sell, qty2, line2)
else:
    if st.button("⏹️ ARRÊTER TOUS LES BOTS"):
        st.session_state.running = False
        st.rerun()
