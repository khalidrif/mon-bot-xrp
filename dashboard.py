import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE CLAIR
st.set_page_config(page_title="XRP Profit Calc", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #000000; }
    [data-testid="stMetricValue"] { color: #2ECC71 !important; font-size: 1.8rem !important; }
    .stButton>button { 
        width: 100%; height: 60px; font-size: 20px !important; 
        border-radius: 15px !important; background-color: #F3BA2F !important;
        color: black !important; border: 2px solid #000 !important; font-weight: bold;
    }
    .profit-box { 
        background-color: #F0FFF4; border: 2px solid #2ECC71; 
        padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 20px;
    }
    input { background-color: #F9F9F9 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #000;'>⚪ CALCUL DU PROFIT NET</h2>", unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })

    # Récupération Solde et Prix
    balance = kraken.fetch_balance()
    usdc_reel = balance['total'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    c1, c2 = st.columns(2)
    c1.metric("DISPO", f"{usdc_reel:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 2. RÉGLAGES TACTILES
    p_in = st.number_input("PRIX ACHAT", value=1.3600, format="%.4f")
    p_out = st.number_input("PRIX VENTE", value=1.3800, format="%.4f")
    vol = st.number_input("VOLUME XRP", value=21.0)

    # --- FONCTION CALCUL PROFIT NET ---
    # Frais Kraken standard : 0.26% à l'achat et 0.26% à la vente
    total_achat = vol * p_in
    total_vente = vol * p_out
    frais = (total_achat * 0.0026) + (total_vente * 0.0026)
    profit_net = (total_vente - total_achat) - frais

    # Affichage du résultat en vert
    st.markdown(f"""
        <div class="profit-box">
            <h3 style="color: #27AE60; margin: 0;">💰 PROFIT NET ESTIMÉ</h3>
            <h2 style="color: #2ECC71; margin: 5px;">+ {profit_net:.2f} $</h2>
            <p style="color: #7F8C8D; font-size: 0.8rem; margin: 0;">(Après frais Kraken de {frais:.2f} $)</p>
        </div>
    """, unsafe_allow_html=True)

    # 3. BOUTONS
    if st.button("🚀 LANCER LA MISSION"):
        try:
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
            kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
            st.balloons()
            st.success("Ordre enregistré !")
        except Exception as e:
            st.error(f"Erreur : {e}")

    if st.button("🚨 ANNULER TOUT"):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Connexion : {e}")

time.sleep(30)
st.rerun()
