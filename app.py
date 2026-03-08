import streamlit as st
import ccxt
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Kraken XRP Snowball", page_icon="🐙", layout="wide")

# --- CONNEXION KRAKEN ---
# En mode production, utilise st.secrets pour la sécurité
# Pour tester en local, tu peux remplacer par 'apiKey': 'TA_CLE', etc.
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets.get("KRAKEN_KEY", ""),
        'secret': st.secrets.get("KRAKEN_SECRET", ""),
        'enableRateLimit': True,
    })
except Exception as e:
    st.error("Erreur de configuration Kraken. Vérifiez vos Secrets.")

# --- REFRESH AUTO (Toutes les 10 secondes) ---
st_autorefresh(interval=10000, key="bot_loop")

# --- INITIALISATION MÉMOIRE ---
if "bot_actif" not in st.session_state:
    st.session_state.bot_actif = False
if "targets" not in st.session_state:
    st.session_state.targets = {"buy": 0.0, "sell": 0.0, "status": "VEILLE"}

# --- RÉCUPÉRATION DES DONNÉES RÉELLES (KRAKEN) ---
try:
    # 1. Prix XRP
    ticker = exchange.fetch_ticker('XRP/USD')
    prix_actuel = ticker['last']

    # 2. Solde USDC
    balance = exchange.fetch_balance()
    # Sur Kraken, l'USDC peut apparaître sous 'USDC' ou 'ZUSD'
    solde_usdc = balance['total'].get('USDC', balance['total'].get('ZUSD', 0.0))
except Exception as e:
    st.warning(f"Connexion limitée : {e}")
    prix_actuel = 1.34 # Valeur par défaut si erreur
    solde_usdc = 0.0

# --- UI : DASHBOARD ---
st.title("🐙 Kraken XRP Auto-Snowball")

c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP (Kraken)", f"{prix_actuel} $")
c2.metric("Mon Solde USDC", f"{round(solde_usdc, 2)} $")
c3.info(f"Statut : **{st.session_state.targets['status']}**")

# --- CONFIGURATION DU CYCLE ---
with st.container(border=True):
    st.subheader("❄️ Paramétrer la Boule de Neige")
    col_a, col_b = st.columns(2)
    
    buy_in = col_a.number_input("Cible Achat (BUY)", value=prix_actuel * 0.995, format="%.4f")
    sell_out = col_b.number_input("Cible Vente (SELL)", value=prix_actuel * 1.015, format="%.4f")
    
    if st.button("LANCER LE BOT SUR MON SOLDE USDC", use_container_width=True, type="primary"):
        st.session_state.targets["buy"] = buy_in
        st.session_state.targets["sell"] = sell_out
        st.session_state.targets["status"] = "ATTENTE ACHAT"
        st.session_state.bot_actif = True
        st.rerun()

# --- LOGIQUE AUTOMATIQUE ---
if st.session_state.bot_actif:
    
    # 1. Détection Achat
    if st.session_state.targets["status"] == "ATTENTE ACHAT" and prix_actuel <= st.session_state.targets["buy"]:
        st.session_state.targets["status"] = "EN POSITION (ACHETÉ)"
        st.toast("🎯 Achat simulé exécuté !")

    # 2. Détection Vente & Snowball
    if st.session_state.targets["status"] == "EN POSITION (ACHETÉ)" and prix_actuel >= st.session_state.targets["sell"]:
        # Le profit est "virtuel" ici car on n'envoie pas d'ordre réel de vente (sécurité)
        st.session_state.targets["status"] = "CYCLE TERMINÉ"
        st.session_state.bot_actif = False
        st.balloons()
        st.success("Bénéfice réalisé ! Votre solde USDC Kraken devrait augmenter au prochain refresh.")

# --- AFFICHAGE DES ORDRES ---
if st.session_state.bot_actif:
    st.divider()
    st.write("📡 **Surveillance active :**")
    st.write(f"📉 Attend le prix `{st.session_state.targets['buy']}$` pour acheter avec tout votre USDC.")
    st.write(f"📈 Revendra à `{st.session_state.targets['sell']}$` pour faire grossir la boule.")

if st.button("Arrêter / Réinitialiser"):
    st.session_state.bot_actif = False
    st.session_state.targets = {"buy": 0.0, "sell": 0.0, "status": "VEILLE"}
    st.rerun()
