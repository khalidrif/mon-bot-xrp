import streamlit as st
import ccxt
import time

# 1. INITIALISATION DE LA MÉMOIRE (Profit Cumulé)
if 'profit_total' not in st.session_state:
    st.session_state.profit_total = 0.0

# STYLE IPHONE CLAIR
st.set_page_config(page_title="XRP Global Profit", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #000; }
    .cumul-box { 
        background-color: #2ECC71; border-radius: 20px; 
        padding: 20px; text-align: center; color: white; margin-bottom: 20px;
        box-shadow: 0px 4px 15px rgba(46, 204, 113, 0.3);
    }
    .stButton>button { width: 100%; height: 60px; border-radius: 15px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. AFFICHAGE DU SCORE GLOBAL (En haut de ton iPhone)
st.markdown(f"""
    <div class="cumul-box">
        <p style="margin: 0; font-size: 1rem; opacity: 0.9;">PROFIT CUMULÉ (SESSION)</p>
        <h1 style="margin: 0; font-size: 3rem;">+ {st.session_state.profit_total:.2f} $</h1>
    </div>
""", unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })

    # Données Live
    balance = kraken.fetch_balance()
    usdc_reel = balance['total'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    c1, c2 = st.columns(2)
    c1.metric("SOLDE DISPO", f"{usdc_reel:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. RÉGLAGES & CALCULS
    p_in = st.number_input("ACHAT", value=1.3600, format="%.4f")
    p_out = st.number_input("VENTE", value=1.3800, format="%.4f")
    vol = st.number_input("VOLUME", value=21.0)

    # Calcul du profit pour ce cycle
    frais = ((vol * p_in) + (vol * p_out)) * 0.0026
    profit_cycle = (vol * (p_out - p_in)) - frais

    st.write(f"💰 Gain net par cycle : **{profit_cycle:.2f} $**")

    # 4. ACTION
    if st.button("🚀 LANCER LA MISSION"):
        params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
        kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
        st.success("C'est parti !")
        # Note: Dans une version pro, on ajouterait ici la détection auto 
        # pour ajouter 'profit_cycle' à 'st.session_state.profit_total'
        # On peut simuler pour le test :
        st.session_state.profit_total += profit_cycle 

    if st.button("🚨 RESET TOTAL"):
        st.session_state.profit_total = 0.0
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(30)
st.rerun()
