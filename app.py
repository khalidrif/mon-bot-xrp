import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Kraken XRP Manager", layout="wide")

# 1. Connexion Kraken via Secrets
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_API_KEY"],
    'secret': st.secrets["KRAKEN_SECRET"],
    'enableRateLimit': True,
})

st.title("🐙 Kraken XRP : Gestionnaire de Bots")

# 2. Affichage Rapide du Solde
bal = exchange.fetch_balance()
st.sidebar.metric("Solde USDC", f"{bal['total'].get('USDC', 0):.2f}")
st.sidebar.metric("Solde XRP", f"{bal['total'].get('XRP', 0):.2f}")

def lancer_bot(id_bot, p_achat, p_vente, qte):
    """Fonction qui gère la logique d'un bot sur une ligne"""
    status = st.empty()
    symbol = 'XRP/USDC'
    
    while True:
        # ÉTAPE A : ACHAT
        status.info(f"🤖 **Bot {id_bot}** : Placement ACHAT à {p_achat}...")
        order_buy = exchange.create_limit_buy_order(symbol, qte, p_achat)
        
        while True:
            check = exchange.fetch_order(order_buy['id'], symbol)
            if check['status'] == 'closed':
                status.success(f"✅ **Bot {id_bot}** : Acheté ! Passage à la Vente...")
                break
            time.sleep(10)
        
        # ÉTAPE B : VENTE
        status.warning(f"🤖 **Bot {id_bot}** : Placement VENTE à {p_vente}...")
        order_sell = exchange.create_limit_sell_order(symbol, qte, p_vente)
        
        while True:
            check = exchange.fetch_order(order_sell['id'], symbol)
            if check['status'] == 'closed':
                status.success(f"💰 **Bot {id_bot}** : Vendu ! Cycle terminé, on repart...")
                break
            time.sleep(10)

# 3. INTERFACE PAR LIGNE
st.write("---")
# --- LIGNE BOT 1 ---
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
p1_a = col1.number_input("Achat Bot 1", value=2.40, format="%.3f")
p1_v = col2.number_input("Vente Bot 1", value=2.50, format="%.3f")
q1 = col3.number_input("Qté Bot 1", value=20.0, key="q1")
if col4.button("▶️ Démarrer Bot 1", key="b1"):
    lancer_bot(1, p1_a, p1_v, q1)

st.write("---")
# --- LIGNE BOT 2 ---
col5, col6, col7, col8 = st.columns([2, 2, 2, 2])
p2_a = col5.number_input("Achat Bot 2", value=2.30, format="%.3f")
p2_v = col6.number_input("Vente Bot 2", value=2.40, format="%.3f")
q2 = col7.number_input("Qté Bot 2", value=20.0, key="q2")
if col8.button("▶️ Démarrer Bot 2", key="b2"):
    lancer_bot(2, p2_a, p2_v, q2)

st.write("---")
st.caption("Note : Pour arrêter un bot, rafraîchissez la page (F5).")
