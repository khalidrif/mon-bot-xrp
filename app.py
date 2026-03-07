import streamlit as st
import ccxt
import time

# Connexion Kraken
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_API_KEY"],
    'secret': st.secrets["KRAKEN_SECRET"],
    'enableRateLimit': True,
})

st.title("XRP Bot Persistant 🐙")

def gerer_ligne_bot(id_bot, p_achat, p_vente, qte):
    """Vérifie l'état actuel sur Kraken avant de lancer un cycle"""
    symbol = 'XRP/USDC'
    status = st.empty()
    
    # 1. RÉCUPÉRER LES ORDRES OUVERTS SUR KRAKEN
    open_orders = exchange.fetch_open_orders(symbol)
    
    # Chercher si un ordre correspondant au prix cible existe déjà
    ordre_existant = next((o for o in open_orders if float(o['price']) in [p_achat, p_vente]), None)

    if ordre_existant:
        status.warning(f"⚠️ Bot {id_bot} : Ordre existant trouvé (ID: {ordre_existant['id']}). Reprise du suivi...")
        current_order = ordre_existant
    else:
        status.info(f"🆕 Bot {id_bot} : Aucun ordre trouvé. Placement Achat à {p_achat}...")
        current_order = exchange.create_limit_buy_order(symbol, qte, p_achat)

    # 2. BOUCLE DE SUIVI PERSISTANTE
    while True:
        check = exchange.fetch_order(current_order['id'], symbol)
        
        if check['status'] == 'closed':
            if check['side'] == 'buy':
                status.success(f"✅ Bot {id_bot} : Achat rempli ! Placement Vente à {p_vente}...")
                current_order = exchange.create_limit_sell_order(symbol, qte, p_vente)
            else:
                status.success(f"💰 Bot {id_bot} : Vente remplie ! Relance Achat à {p_achat}...")
                current_order = exchange.create_limit_buy_order(symbol, qte, p_achat)
        
        time.sleep(15)

# --- INTERFACE ---
col1, col2, col3, col4 = st.columns([2,2,2,1])
p1_a = col1.number_input("Prix Achat", value=2.40, format="%.3f", key="p1a")
p1_v = col2.number_input("Prix Vente", value=2.50, format="%.3f", key="p1v")
q1 = col3.number_input("Quantité", value=20.0, key="q1")

if col4.button("▶️ Start/Sync", key="btn1"):
    gerer_ligne_bot(1, p1_a, p1_v, q1)
