import streamlit as st
import krakenex
import time

# 1. CONNEXION
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

st.set_page_config(page_title="XRP Snowball Tracker", layout="wide")
st.title("❄️ XRP SNOWBALL : SUIVI DES GAINS")

# 2. PARAMÈTRES
with st.sidebar:
    st.header("Configuration")
    p_achat = st.number_input("Prix d'Achat (USDC)", value=1.0500, format="%.4f")
    p_vente = st.number_input("Prix de Vente (USDC)", value=1.1000, format="%.4f")
    st.divider()
    # Calcul du profit théorique par cycle
    profit_pct = ((p_vente / p_achat) - 1) * 100
    st.info(f"📈 Profit par cycle : **+{profit_pct:.2f}%**")

# Initialisation des variables de session
if 'running' not in st.session_state: st.session_state.running = False
if 'total_gain' not in st.session_state: st.session_state.total_gain = 0.0
if 'start_balance' not in st.session_state: st.session_state.start_balance = 0.0

# 3. DASHBOARD DE PERFORMANCE
c1, c2, c3 = st.columns(3)
status_placeholder = st.empty()

# Récupération du solde pour le dashboard
try:
    bal = k.query_private('Balance')['result']
    usdc_actuel = float(bal.get('USDC', 0))
    xrp_actuel = float(bal.get('XRP', 0))
    
    if st.session_state.start_balance == 0: 
        st.session_state.start_balance = usdc_actuel

    c1.metric("SOLDE USDC", f"{usdc_actuel:.2f} $")
    c2.metric("SOLDE XRP", f"{xrp_actuel:.2f}")
    c3.metric("GAIN TOTAL", f"+{usdc_actuel - st.session_state.start_balance:.4f} $", delta=f"{profit_pct:.2f}%")
except:
    st.warning("En attente des données Kraken...")

# 4. CONTRÔLES
col_a, col_b = st.columns(2)
if col_a.button("▶️ DÉMARRER LA BOUCLE", use_container_width=True, type="primary"):
    st.session_state.running = True
if col_b.button("⏹️ ARRÊTER LE BOT", use_container_width=True):
    st.session_state.running = False
    st.rerun()

# 5. LOGIQUE DU BOT
if st.session_state.running:
    while st.session_state.running:
        try:
            # Vérification des ordres ouverts
            res = k.query_private('OpenOrders')
            ordres = res.get('result', {}).get('open', {})

            if not ordres:
                # Calcul de la Boule de Neige
                bal = k.query_private('Balance')['result']
                usdc_dispo = float(bal.get('USDC', 0))
                
                # On utilise 99% du solde (pour laisser de la place aux frais Kraken)
                vol_max = (usdc_dispo * 0.99) / p_achat
                
                if vol_max >= 10: # Minimum requis par Kraken
                    status_placeholder.success(f"🔄 CYCLE TERMINÉ ! Relance avec {vol_max:.2f} XRP")
                    
                    params = {
                        'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
                        'price': str(round(p_achat, 4)), 'volume': str(round(vol_max, 1)),
                        'close[ordertype]': 'limit', 'close[price]': str(round(p_vente, 4)), 'close[type]': 'sell'
                    }
                    k.query_private('AddOrder', params)
                    time.sleep(2) # Pause sécurité
                else:
                    status_placeholder.error("Solde USDC insuffisant pour le minimum Kraken (10 XRP).")
            else:
                for oid, det in ordres.items():
                    status_placeholder.info(f"⏳ Ordre actif : {det['descr']['order']}")

        except Exception as e:
            st.error(f"Erreur : {e}")

        time.sleep(20) # Scan toutes les 20 secondes
        st.rerun()

else:
    status_placeholder.write("💤 Le bot est en pause.")
