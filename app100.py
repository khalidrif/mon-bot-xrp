
import streamlit as st
import krakenex
import time

# 1. STYLE JAUNE & NOIR
st.set_page_config(page_title="XRP Test Bot", layout="centered")
st.markdown("<style>.stApp { background-color: #000; color: #F3BA2F; }</style>", unsafe_allow_html=True)

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# --- INITIALISATION DE SÉCURITÉ ---
usdc = 0.0  # La variable existe maintenant quoi qu'il arrive

st.title("🟡 TEST BOT XRP : 1 SEUL CYCLE")

# 2. ESSAI DE CONNEXION
try:
    res = k.query_private('Balance')
    if res and 'result' in res:
        usdc = float(res['result'].get('USDC', 0))
        st.success(f"✅ Connecté ! Solde : {usdc:.2f} USDC")
    else:
        st.warning("⏳ Kraken en attente (Maintenance du 6 mars...)")
except:
    st.error("❌ Erreur de liaison API")

st.divider()

# 3. RÉGLAGES (C'est toi qui programmes)
col1, col2 = st.columns(2)
p_in = col1.number_input("PRIX ACHAT", value=1.3600, format="%.4f")
p_out = col2.number_input("PRIX VENTE", value=1.4000, format="%.4f")

# On calcule le volume pour utiliser TOUT ton solde (avec 1.5% de marge)
if usdc > 10:
    vol_auto = (usdc * 0.985) / p_in
else:
    vol_auto = 22.0 # Valeur de secours pour test

vol = st.number_input("VOLUME XRP", value=float(round(vol_auto, 1)))

# 4. LANCEMENT
if st.button("🚀 LANCER LE TEST", type="primary", use_container_width=True):
    params = {
        'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
        'price': str(p_in), 'volume': str(vol),
        'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
    }
    reponse = k.query_private('AddOrder', params)
    
    if reponse.get('error'):
        st.error(f"Refus : {reponse['error']}")
    else:
        st.balloons()
        st.success("✅ ORDRE PLACÉ SUR KRAKEN !")

# 5. MONITORING
st.divider()
try:
    ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})
    if ordres:
        for oid, det in ordres.items():
            st.info(f"⏳ EN COURS : {det['descr']['order']}")
    else:
        st.write("Aucun ordre actif.")
except: pass

time.sleep(15)
st.rerun()
