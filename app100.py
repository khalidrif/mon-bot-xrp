import streamlit as st
import krakenex
import time

# 1. STYLE & SETUP
st.set_page_config(page_title="XRP Test 100$", layout="centered")
st.markdown("<style>.stApp { background-color: #000; color: #F3BA2F; }</style>", unsafe_allow_html=True)

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# Initialisation de sécurité
usdc_reel = 0.0

st.title("🟡 TEST ÉCLAIREUR : 100 $")

# 2. VÉRIFICATION CONNEXION
try:
    res = k.query_private('Balance')
    if res and 'result' in res:
        usdc_reel = float(res['result'].get('USDC', 0))
        st.success(f"✅ Kraken Répond ! Solde : {usdc_reel:.2f} USDC")
    else:
        st.warning("⏳ Kraken en attente... (Maintenance 6 Mars)")
except:
    st.error("❌ Erreur de liaison API")

st.divider()

# 3. RÉGLAGE DU TEST (100$)
col1, col2 = st.columns(2)
p_in = col1.number_input("ACHAT (Prix Bas)", value=1.3600, format="%.4f")
p_out = col2.number_input("VENTE (Prix Haut)", value=1.4000, format="%.4f")

# On fixe le volume pour environ 100$ (100 / 1.36 = ~73 XRP)
vol_test = 73.0 
st.write(f"📦 Test sur **100 $** (~{vol_test} XRP)")

# 4. BOUTON DE LANCEMENT
if st.button("🚀 LANCER L'ÉCLAIREUR (100$)", type="primary", use_container_width=True):
    # On vérifie si on a au moins les 100$
    if usdc_reel >= 100 or usdc_reel == 0: # 0 si l'API est encore en pause
        params = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
            'price': str(p_in), 'volume': str(vol_test),
            'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
        }
        reponse = k.query_private('AddOrder', params)
        
        if reponse.get('error'):
            st.error(f"Refus : {reponse['error']}")
        else:
            st.balloons()
            st.success("✅ ORDRE DE 100$ PLACÉ !")
    else:
        st.error(f"Solde insuffisant pour 100$ (Actuel: {usdc_reel}$)")

# 5. ÉTAT DE L'ORDRE
st.divider()
try:
    ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})
    if ordres:
        for oid, det in ordres.items():
            st.info(f"⏳ EN MISSION : {det['descr']['order']}")
    else:
        st.write("Aucun ordre actif.")
except: pass

time.sleep(15)
st.rerun()
