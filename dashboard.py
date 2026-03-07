import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM (Bleu pour le Solde, Orange pour le Prix)
st.set_page_config(page_title="XRP Sniper Pro", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    
    /* SOLDE DISPO EN BLEU */
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] { 
        color: #007AFF !important; font-weight: 800 !important; font-size: 2.2rem !important; 
    }
    /* PRIX XRP EN ORANGE */
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] { 
        color: #FF9500 !important; font-weight: 800 !important; font-size: 2.2rem !important; 
    }
    
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 25px; padding: 20px; text-align: center; color: white; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 65px; border-radius: 20px !important; background-color: #F3BA2F !important; font-weight: bold; font-size: 20px !important; color: black !important; }
    div[data-testid="stMetric"] { background-color: white; padding: 15px; border-radius: 20px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05); border: 1px solid #DEE2E6; }
    </style>
    """, unsafe_allow_html=True)

if 'profit_total' not in st.session_state: 
    st.session_state.profit_total = 0.0

st.markdown(f'<div class="cumul-box"><p style="margin:0">PROFIT TOTAL</p><h1>+ {st.session_state.profit_total:.2f} $</h1></div>', unsafe_allow_html=True)

try:
    # CONNEXION KRAKEN
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_reel = balance['total'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    col1, col2 = st.columns(2)
    col1.metric("DISPO USDC", f"{usdc_reel:.2f} $")
    col2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # --- CONFIGURATION DU SNIPER ---
    st.markdown("### 🚜 RÉGLAGE DE LA MISSION")
    p_in = st.number_input("PRIX ACHAT (Cible)", value=1.3600, format="%.4f")
    p_out = st.number_input("PRIX VENTE (Profit)", value=1.3800, format="%.4f")
    
    # CALCUL DU VOLUME (95% du solde pour passer le minimum Kraken)
    vol_test = (usdc_reel * 0.95) / prix_actuel if usdc_reel > 14 else 0
    vol_final = st.number_input("VOLUME XRP", value=float(round(vol_test, 1)))

    # --- BOUTON DE LANCEMENT ---
    if st.button("🚀 ACTIVER LE SNIPER"):
        if vol_final >= 10.0:
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
            kraken.create_limit_buy_order('XRP/USDC', vol_final, p_in, params)
            st.balloons()
            st.success(f"✅ Mission lancée : {vol_final} XRP à {p_in}$")
        else:
            st.error("Solde trop petit (Min 14$ requis pour 10 XRP)")

    st.divider()
    
    # --- AFFICHAGE DES MISSIONS EN COURS ---
    st.markdown("### 📦 MISSIONS EN COURS")
    open_orders = kraken.fetch_open_orders('XRP/USDC')
    if open_orders:
        for order in open_orders:
            st.info(f"🎯 {order['side'].upper()} {order['amount']} XRP @ {order['price']} $")
    else:
        st.write("Aucune mission active. Ton argent dort.")

    if st.button("🚨 ANNULER TOUT / RESET"):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Liaison : {e}")

time.sleep(30)
st.rerun()
