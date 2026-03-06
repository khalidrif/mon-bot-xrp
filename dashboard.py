import streamlit as st
import krakenex
import time
from datetime import datetime

# 1. CONFIGURATION
st.set_page_config(page_title="XRP Snowball Pro", layout="wide")
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# Initialisation de l'historique
if 'logs' not in st.session_state: st.session_state.logs = []
if 'running' not in st.session_state: st.session_state.running = False
if 'last_balance' not in st.session_state: st.session_state.last_balance = 0.0

st.title("❄️ XRP SNOWBALL COMPTEUR")

# 2. RÉGLAGES (SIDEBAR)
with st.sidebar:
    st.header("⚙️ Configuration")
    p_achat = st.number_input("Prix Achat", value=1.0500, format="%.4f")
    p_vente = st.number_input("Prix Vente", value=1.1000, format="%.4f")
    st.divider()
    gain_cycle = ((p_vente / p_achat) - 1) * 100
    st.info(f"Gain théorique : **+{gain_cycle:.2f}%** / cycle")

# 3. DASHBOARD DE PERFORMANCE
try:
    bal = k.query_private('Balance')['result']
    usdc_actuel = float(bal.get('USDC', 0))
    xrp_actuel = float(bal.get('XRP', 0))
    
    c1, c2, c3 = st.columns(3)
    c1.metric("SOLDE USDC", f"{usdc_actuel:.2f} $")
    c2.metric("SOLDE XRP", f"{xrp_actuel:.2f}")
    
    # Détection de profit pour l'historique
    if st.session_state.last_balance > 0 and usdc_actuel > st.session_state.last_balance:
        profit = usdc_actuel - st.session_state.last_balance
        now = datetime.now().strftime("%H:%M:%S")
        st.session_state.logs.append(f"✅ [{now}] Vente validée ! Profit : +{profit:.4f} USDC")
    
    st.session_state.last_balance = usdc_actuel
    c3.metric("ETAT DU BOT", "ACTIF" if st.session_state.running else "PAUSE")
except:
    st.error("Connexion Kraken impossible.")

# 4. COMMANDES
col_a, col_b = st.columns(2)
if col_a.button("▶️ DÉMARRER", use_container_width=True, type="primary"):
    st.session_state.running = True
if col_b.button("⏹️ ARRÊTER", use_container_width=True):
    st.session_state.running = False
    st.rerun()

# 5. BOUCLE DU BOT
status = st.empty()

if st.session_state.running:
    try:
        res = k.query_private('OpenOrders')
        ordres = res.get('result', {}).get('open', {})

        if not ordres:
            # Calcul Boule de Neige (Volume max avec USDC dispo)
            vol_max = (usdc_actuel * 0.98) / p_achat # 2% de marge pour frais
            
            if vol_max >= 10:
                params = {
                    'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
                    'price': str(round(p_achat, 4)), 'volume': str(round(vol_max, 1)),
                    'close[ordertype]': 'limit', 'close[price]': str(round(p_vente, 4)), 'close[type]': 'sell'
                }
                k.query_private('AddOrder', params)
                status.success("🔄 Nouveau cycle lancé !")
            else:
                status.error("Solde USDC trop faible pour 10 XRP minimum.")
        else:
            for oid, det in ordres.items():
                status.info(f"⏳ En cours : {det['descr']['order']}")

    except Exception as e:
        status.error(f"Erreur : {e}")

    time.sleep(15)
    st.rerun()

# 6. HISTORIQUE DES VENTES
st.divider()
st.subheader("📜 Historique des cycles")
if st.session_state.logs:
    for log in reversed(st.session_state.logs):
        st.write(log)
else:
    st.write("Aucune vente enregistrée pour le moment.")
