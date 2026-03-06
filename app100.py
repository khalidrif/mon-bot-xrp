import streamlit as st
import krakenex
import time

# 1. STYLE IPHONE (Gros boutons, Noir & Jaune)
st.set_page_config(page_title="XRP Pocket Bot", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #F3BA2F; }
    [data-testid="stMetricValue"] { color: #F3BA2F !important; font-size: 2rem !important; }
    .stButton>button { 
        width: 100%; height: 60px; font-size: 20px !important; 
        border-radius: 15px !important; background-color: #F3BA2F !important;
        color: black !important; border: none !important; font-weight: bold;
    }
    input { background-color: #121212 !important; color: white !important; border: 1px solid #F3BA2F !important; }
    .stAlert { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. INITIALISATION API & VARIABLES
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])
usdc = 0.0  # Défini ici pour éviter l'erreur "not defined"

st.markdown("<h1 style='text-align: center; color: #F3BA2F;'>🟡 XRP COMMAND</h1>", unsafe_allow_html=True)

# 3. VÉRIFICATION RÉELLE DE LA CONNEXION
try:
    res = k.query_private('Balance')
    if res.get('error'):
        st.error(f"❌ KRAKEN DIT : {res['error']}")
    elif res.get('result'):
        usdc = float(res['result'].get('USDC', 0))
        st.success(f"✅ CONNECTÉ : {usdc:.2f} USDC")
    else:
        st.warning("⏳ CONNEXION KRAKEN... (Vérifie tes clés API)")
except Exception as e:
    st.error(f"📡 ERREUR RÉSEAU : {e}")

st.divider()

# 4. RÉGLAGES DU BOT (100$ ou 29$)
col1, col2 = st.columns(2)
p_in = col1.number_input("ACHAT (Prix Bas)", value=1.3500, format="%.4f", step=0.0001)
p_out = col2.number_input("VENTE (Prix Haut)", value=1.4000, format="%.4f", step=0.0001)

# Calcul automatique du volume (100$ par défaut ou ton solde max)
budget_test = usdc if usdc > 10 else 100.0
vol_auto = (budget_test * 0.98) / p_in
vol = st.number_input("VOLUME XRP", value=float(round(vol_auto, 1)))

# 5. BOUTONS D'ACTION IPHONE
if st.button("🚀 LANCER LE BOT (UN PAR UN)"):
    params = {
        'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
        'price': str(p_in), 'volume': str(vol),
        'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
    }
    reponse = k.query_private('AddOrder', params)
    if reponse.get('error'):
        st.error(f"Refusé : {reponse['error']}")
    else:
        st.balloons()
        st.success("✅ MISSION LANCÉE SUR KRAKEN !")

st.write("") # Espace pour le pouce
if st.button("🚨 STOP / ANNULER TOUT"):
    k.query_private('CancelAll')
    st.rerun()

# 6. ÉTAT DES ORDRES EN COURS
st.divider()
try:
    ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})
    if ordres:
        st.subheader("📦 Missions en cours :")
        for oid, det in ordres.items():
            st.info(f"🎯 {det['descr']['order']}")
    else:
        st.write("Aucun ordre actif.")
except:
    pass

# Auto-refresh toutes les 20 secondes
time.sleep(20)
st.rerun()
