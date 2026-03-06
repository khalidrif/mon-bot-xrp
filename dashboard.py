import streamlit as st
import krakenex
import time

# 1. CONNEXION
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

st.title("🔄 XRP INFINITE LOOP BOT")

# 2. PARAMÈTRES
with st.sidebar:
    st.header("Configuration")
    p_achat = st.number_input("Prix Achat", value=1.0500, format="%.4f")
    p_vente = st.number_input("Prix Vente", value=1.1000, format="%.4f")
    vol = st.number_input("Volume XRP", value=10.0)
    delay = st.slider("Pause scan (sec)", 5, 60, 10)

# 3. ÉTAT DU BOT
if 'running' not in st.session_state:
    st.session_state.running = False

col_run, col_stop = st.columns(2)
if col_run.button("▶️ DÉMARRER LA BOUCLE", use_container_width=True):
    st.session_state.running = True

if col_stop.button("⏹️ ARRÊTER LE BOT", use_container_width=True):
    st.session_state.running = False
    st.rerun()

# 4. LOGIQUE DE LA BOUCLE
status_area = st.empty() # Zone pour afficher ce que fait le bot

if st.session_state.running:
    status_area.info("🤖 Bot en ligne. Scan des ordres...")
    
    while st.session_state.running:
        try:
            # Vérifier les ordres ouverts
            res = k.query_private('OpenOrders')
            ordres = res.get('result', {}).get('open', {})
            
            # SI AUCUN ORDRE : On relance un cycle d'achat
            if not ordres:
                status_area.warning("🔄 Aucun ordre trouvé. Création d'un cycle Achat -> Vente...")
                params = {
                    'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 
                    'price': str(p_achat), 'volume': str(vol),
                    'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
                }
                k.query_private('AddOrder', params)
                st.success("✅ Nouveau cycle placé !")
            
            else:
                # On affiche l'ordre en cours
                for oid, info in ordres.items():
                    status_area.info(f"⏳ En attente : {info['descr']['order']}")
            
        except Exception as e:
            st.error(f"Erreur : {e}")
        
        time.sleep(delay) # Pause pour ne pas saturer l'API
        
else:
    status_area.write("💤 Bot en sommeil.")

# 5. AFFICHAGE SIMPLE DU SOLDE
st.divider()
try:
    bal = k.query_private('Balance')['result']
    st.write(f"💰 **Portefeuille :** {bal.get('USDC', '0')} USDC | {bal.get('XRP', '0')} XRP")
except: pass
