import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE FOND BLANC (Pro & Clair)
st.set_page_config(page_title="XRP Light Command", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #000000; }
    [data-testid="stMetricValue"] { color: #F3BA2F !important; font-size: 1.8rem !important; }
    .stButton>button { 
        width: 100%; height: 60px; font-size: 20px !important; 
        border-radius: 15px !important; background-color: #F3BA2F !important;
        color: black !important; border: 2px solid #000 !important; font-weight: bold;
    }
    input { background-color: #F9F9F9 !important; color: black !important; border: 1px solid #CCC !important; }
    label { color: black !important; font-weight: bold; }
    .stAlert { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #000;'>⚪ XRP COMMAND</h1>", unsafe_allow_html=True)

# 2. CONNEXION SÉCURISÉE CCXT
try:
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })

    # Récupération du solde et du prix
    balance = kraken.fetch_balance()
    usdc_reel = balance['total'].get('USDC', 0.0)
    
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last']) if ticker['last'] else 1.3500
    
    c1, c2 = st.columns(2)
    c1.metric("DISPO", f"{usdc_reel:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. RÉGLAGES (Ton test 1.36 / 1.38)
    n_grids = st.number_input("NOMBRE DE BOTS", value=1, min_value=1)
    p_min = st.number_input("PRIX ACHAT", value=1.3600, format="%.4f")
    p_out = st.number_input("PRIX VENTE", value=1.3800, format="%.4f")

    # Calcul Volume Anti-Crash
    vol_calcule = (usdc_reel * 0.98 / n_grids) / prix_actuel if prix_actuel > 0 else 21.0
    vol_final = st.number_input("VOLUME XRP", value=max(float(round(vol_calcule, 1)), 10.5))

    # 4. BOUTON LANCEMENT
    if st.button("🚀 DÉPLOYER LA MISSION"):
        if usdc_reel < (vol_final * p_min):
            st.error("Solde insuffisant !")
        else:
            try:
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol_final, p_min, params)
                st.balloons()
                st.success(f"✅ Mission lancée sur le blanc !")
            except Exception as e:
                st.error(f"Erreur : {e}")

    # 5. BOUTON PANIQUE (Rouge sur Blanc)
    st.write("")
    if st.button("🚨 ANNULER TOUT / RESET"):
        kraken.cancel_all_orders('XRP/USDC')
        st.warning("Tout est annulé.")
        st.rerun()

except Exception as e:
    st.error(f"❌ Connexion impossible : {e}")

time.sleep(30)
st.rerun()
