import streamlit as st
import krakenex
import time

# 1. CONFIGURATION VISUELLE (Style Jaune & Noir)
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
    </style>
    """, unsafe_allow_html=True)

# 2. INITIALISATION API & VARIABLES DE SÉCURITÉ
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])
usdc = 0.0  # Défini par défaut pour éviter l'erreur "not defined"

st.markdown("<h1 style='text-align: center; color: #F3BA2F;'>🟡 XRP COMMAND</h1>", unsafe_allow_html=True)

# 3. TENTATIVE DE CONNEXION AVEC DIAGNOSTIC
try:
    res = k.query_private('Balance')
    if res.get('error'):
        # Affiche l'erreur réelle de Kraken (ex: EAPI:Invalid key)
        st.error(f"❌ KRAKEN DIT : {res['error']}")
    elif res.get('result'):
        # Succès : on récupère le vrai solde
        usdc = float(res['result'].get('USDC', 0))
        st.success(f"✅ CONNECTÉ : {usdc:.2f} USDC")
    else:
        # Cas où Kraken répond vide
        st.warning("⏳ CONNEXION KRAKEN... (Maintenance en cours ou API saturée)")
except Exception as e:
    st.error(f"📡 ERREUR RÉSEAU : {e}")

st.divider()

# 4. RÉGLAGES (Utilise 100$ par défaut si le solde est illisible)
budget_test = usdc if usdc > 10 else 100.0
p_in = st.number_input("ACHAT (Prix Bas)", value=1.3500, format="%.4f")
p_out = st.number_input("VENTE (Prix Haut)", value=1.4000, format="%.4f")
vol = st.number_input("VOLUME XRP", value=float(round((budget_test * 0.98) / p_in, 1)))

# 5. BOUTON D'ACTION
if st.button("🚀 LANCER LE BOT"):
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

# Bouton de reset
if st.button("🚨 STOP / ANNULER TOUT"):
    k.query_private('CancelAll')
    st.rerun()

# 6. RAFRAÎCHISSEMENT AUTO
time.sleep(20)
st.rerun()
