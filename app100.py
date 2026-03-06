import streamlit as st
import krakenex
import time

# 1. CONFIGURATION MOBILE & STYLE
st.set_page_config(page_title="XRP Pocket Bot", layout="centered")

# CSS spécial pour iPhone (Gros boutons, texte clair, fond noir)
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #F3BA2F !important; }
    .stButton>button { 
        width: 100%; 
        height: 60px; 
        font-size: 20px !important; 
        border-radius: 15px !important;
        background-color: #F3BA2F !important;
        color: black !important;
        border: none !important;
    }
    input { font-size: 18px !important; height: 50px !important; }
    .stAlert { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])
usdc = 0.0

# 2. HEADER SIMPLE
st.markdown("<h2 style='text-align: center; color: #F3BA2F;'>🟡 XRP POCKET BOT</h2>", unsafe_allow_html=True)

try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})['result']['XRPUSDC']
    prix_actuel = float(ticker['c'])
    res = k.query_private('Balance')
    if res and 'result' in res:
        usdc = float(res['result'].get('USDC', 0))
        st.metric("MON SOLDE", f"{usdc:.2f} USDC")
        st.metric("PRIX XRP", f"{prix_actuel:.4f} $")
    else:
        st.warning("⏳ Connexion Kraken... (Maintenance)")
except:
    st.error("📡 Erreur réseau")

st.divider()

# 3. RÉGLAGES TACTILES
p_in = st.number_input("ACHAT (Prix Bas)", value=1.3600, format="%.4f", step=0.0001)
p_out = st.number_input("VENTE (Prix Haut)", value=1.4000, format="%.4f", step=0.0001)
vol = st.number_input("VOLUME XRP", value=73.0, step=1.0) # Défaut pour 100$

# 4. GROS BOUTONS D'ACTION
if st.button("🚀 LANCER LE BOT"):
    params = {
        'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
        'price': str(p_in), 'volume': str(vol),
        'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
    }
    reponse = k.query_private('AddOrder', params)
    if reponse.get('error'):
        st.error(f"Erreur : {reponse['error']}")
    else:
        st.success("✅ ORDRE ENVOYÉ !")

st.write("") # Espace pour le pouce
if st.button("🚨 STOP / ANNULER"):
    k.query_private('CancelAll')
    st.rerun()

# 5. ÉTAT SIMPLIFIÉ
try:
    ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})
    if ordres:
        for oid, det in ordres.items():
            st.info(f"🎯 {det['descr']['order']}")
except: pass

time.sleep(15)
st.rerun()
