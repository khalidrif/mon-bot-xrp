import streamlit as st
import ccxt
import time

# 1. Connexion Kraken
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_API_KEY"],
    'secret': st.secrets["KRAKEN_SECRET"],
    'enableRateLimit': True,
})

st.title("XRP Bot Dashboard 🐙")

# 2. Affichage des Soldes
balance = exchange.fetch_balance()
col_bal1, col_bal2 = st.columns(2)
col_bal1.metric("Solde XRP", f"{balance['total'].get('XRP', 0):.2f}")
col_bal2.metric("Solde USDC", f"{balance['total'].get('USDC', 0):.2f}")

st.divider()

# 3. Configuration des deux bots
st.subheader("⚙️ Configuration")
c1, c2, c3 = st.columns(3)
with c1:
    h_buy = st.number_input("Bot 1 : Achat", value=2.450, format="%.3f")
    b_buy = st.number_input("Bot 2 : Achat", value=2.350, format="%.3f")
with c2:
    h_sell = st.number_input("Bot 1 : Vente", value=2.550, format="%.3f")
    b_sell = st.number_input("Bot 2 : Vente", value=2.450, format="%.3f")
with c3:
    h_qty = st.number_input("Bot 1 : Qté", value=20.0, key="q1")
    b_qty = st.number_input("Bot 2 : Qté", value=20.0, key="q2")

# 4. Boutons et Suivi
st.divider()
col_btn1, col_btn2 = st.columns([1, 4])
start = col_btn1.button("▶️ DÉMARRER")
stop = col_btn2.button("⏹️ ARRÊTER")

log1 = st.empty()
log2 = st.empty()

if start:
    st.session_state.active = True
if stop:
    st.session_state.active = False

# 5. Boucle de fonctionnement
if st.session_state.get('active'):
    st.success("Bots en cours d'exécution...")
    while st.session_state.active:
        # Affichage simple de l'état
        log1.info(f"🤖 **Bot 1** : Surveille Achat à {h_buy} / Vente à {h_sell}")
        log2.info(f"🤖 **Bot 2** : Surveille Achat à {b_buy} / Vente à {b_sell}")
        
        # Ici le bot vérifie les ordres sur Kraken (fetch_open_orders)
        # Puis il attend 10 secondes avant de recommencer
        time.sleep(10)
else:
    st.write("Bots à l'arrêt.")
