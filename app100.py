import streamlit as st
import krakenex
import time

# 1. STYLE NOIR & OR
st.set_page_config(page_title="XRP 50-GRID COMMAND", layout="wide")
st.markdown("<style>.stApp { background-color: #000; color: #F3BA2F; }</style>", unsafe_allow_html=True)

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

st.title("🎖️ XRP MEGA-GRID : 50 BOTS")

# 2. DASHBOARD LIVE
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})['result']['XRPUSDC']
    prix_actuel = float(ticker['c'])
    bal = k.query_private('Balance')['result']
    usdc = float(bal.get('USDC', 0))
    
    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX XRP", f"{prix_actuel:.4f} $")
    c2.metric("SOLDE USDC", f"{usdc:.2f} $")
    c3.metric("BOTS POSSIBLES (60$)", int(usdc / 60))
except:
    st.warning("⏳ Connexion Kraken... (Maintenance en cours)")

st.divider()

# 3. CONFIGURATION DE LA GRILLE
with st.container():
    col_a, col_b, col_c = st.columns(3)
    p_min = col_a.number_input("PRIX BAS", value=1.2500, format="%.4f")
    p_max = col_b.number_input("PRIX HAUT", value=1.4500, format="%.4f")
    vol_xrp = col_c.number_input("XRP PAR PALIER (Budget ~60$)", value=44.0)

# 4. ACTION : DÉPLOIEMENT DES 50 BOTS
if st.button("🚀 DÉPLOYER LES 50 BOTS (3000$)", use_container_width=True, type="primary"):
    # On calcule l'écart entre 50 niveaux
    intervalle = (p_max - p_min) / 49 
    barre = st.progress(0)
    info_envoi = st.empty()
    
    for i in range(50):
        p_achat = round(p_min + (i * intervalle), 4)
        p_vente = round(p_achat + (intervalle * 2), 4) # Vente 2 paliers au dessus
        
        params = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
            'price': str(p_achat), 'volume': str(vol_xrp),
            'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
        }
        
        # ENVOI AVEC PAUSE (Crucial pour 50 ordres !)
        k.query_private('AddOrder', params)
        time.sleep(0.7) # Pause de sécurité pour l'API
        
        barre.progress((i + 1) / 50)
        info_envoi.write(f"📡 Envoi du Bot {i+1}/50 au prix {p_achat} $")
        
    st.success("✅ Armée de 50 bots opérationnelle !")

if st.button("🚨 STOP & ANNULER TOUT", use_container_width=True):
    k.query_private('CancelAll')
    st.rerun()

# 5. LISTE DES ORDRES ACTIFS
st.divider()
try:
    ordres = k.query_private('OpenOrders')['result']['open']
    if ordres:
        st.subheader(f"📦 {len(ordres)} Paliers en attente sur Kraken")
        with st.expander("Voir le détail des ordres"):
            for oid, det in ordres.items():
                st.caption(f"📍 {det['descr']['order']}")
except: pass

time.sleep(20)
st.rerun()
