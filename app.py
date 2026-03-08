import streamlit as st
import ccxt
import time
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Kraken XRP Snowball", page_icon="🐙")

# --- CONNEXION KRAKEN (Public pour le prix) ---
exchange = ccxt.kraken()

# --- REFRESH AUTO (Toutes les 10 secondes) ---
st_autorefresh(interval=10000, key="kraken_refresh")

# --- INITIALISATION MÉMOIRE ---
if "capital" not in st.session_state:
    st.session_state.capital = 100.0  # Mise de départ
if "bot_actif" not in st.session_state:
    st.session_state.bot_actif = False
if "stats" not in st.session_state:
    st.session_state.stats = {"achat": 0.0, "vente": 0.0, "status": "VEILLE"}

# --- RÉCUPÉRATION PRIX RÉEL ---
try:
    ticker = exchange.fetch_ticker('XRP/USD')
    prix_actuel = ticker['last']
except Exception as e:
    st.error(f"Erreur connexion Kraken : {e}")
    prix_actuel = 0.0

# --- UI PRINCIPALE ---
st.title("🐙 Kraken Auto-Snowball")
st.subheader(f"Prix XRP Actuel : `{prix_actuel} $`")

col1, col2 = st.columns(2)
with col1:
    st.metric("Capital Actuel", f"{round(st.session_state.capital, 2)} $")
with col2:
    st.info(f"Statut : **{st.session_state.stats['status']}**")

# --- RÉGLAGES DES CIBLES ---
with st.container(border=True):
    st.write("🎯 **Configurer le prochain cycle**")
    c1, c2 = st.columns(2)
    buy_target = c1.number_input("Acheter si prix baisse à", value=prix_actuel * 0.99, format="%.4f")
    sell_target = c2.number_input("Vendre si prix monte à", value=prix_actuel * 1.02, format="%.4f")
    
    if st.button("DÉMARRER LE BOT", use_container_width=True, type="primary"):
        st.session_state.stats["achat"] = buy_target
        st.session_state.stats["vente"] = sell_target
        st.session_state.stats["status"] = "ATTENTE ACHAT"
        st.session_state.bot_actif = True
        st.rerun()

# --- LOGIQUE AUTOMATIQUE (BOULE DE NEIGE) ---
if st.session_state.bot_actif:
    
    # 1. DÉCLENCHEMENT ACHAT
    if st.session_state.stats["status"] == "ATTENTE ACHAT" and prix_actuel <= st.session_state.stats["achat"]:
        st.session_state.stats["status"] = "EN POSITION (ACHETÉ)"
        st.toast("✅ Achat simulé exécuté !")

    # 2. DÉCLENCHEMENT VENTE & SNOWBALL
    if st.session_state.stats["status"] == "EN POSITION (ACHETÉ)" and prix_actuel >= st.session_state.stats["vente"]:
        # Calcul du nouveau capital (Mise x Ratio de hausse)
        ratio = st.session_state.stats["vente"] / st.session_state.stats["achat"]
        nouveau_capital = st.session_state.capital * ratio
        
        # Mise à jour
        st.session_state.capital = nouveau_capital
        st.session_state.stats["status"] = "CYCLE TERMINÉ"
        st.session_state.bot_actif = False
        st.balloons()
        st.success(f"Bénéfice réalisé ! Nouveau capital : {round(nouveau_capital, 2)}$")

# --- HISTORIQUE ---
if st.session_state.stats["achat"] > 0:
    st.divider()
    st.write("📊 **Ordres en surveillance :**")
    st.write(f"- Cible Achat : `{st.session_state.stats['achat']}$`")
    st.write(f"- Cible Vente : `{st.session_state.stats['vente']}$` (Profit attendu : {round((st.session_state.stats['vente']/st.session_state.stats['achat'] - 1)*100, 2)}%)")

if st.button("Réinitialiser tout"):
    st.session_state.clear()
    st.rerun()
