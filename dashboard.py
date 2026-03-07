import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM
st.set_page_config(page_title="XRP Double Sniper", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] { color: #007AFF !important; font-size: 2.2rem !important; }
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] { color: #FF9500 !important; font-size: 2.2rem !important; }
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 25px; padding: 20px; text-align: center; color: white; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 60px; border-radius: 20px !important; background-color: #F3BA2F !important; font-weight: bold; }
    .bot-card { background: white; padding: 15px; border-radius: 15px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0
st.markdown(f'<div class="cumul-box"><h1>+ {st.session_state.profit_total:.2f} $</h1></div>', unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_reel = balance['total'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    col1, col2 = st.columns(2)
    col1.metric("DISPO USDC", f"{usdc_reel:.2f} $")
    col2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # --- CONFIGURATION MANUELLE DES 2 BOTS ---
    st.markdown("### 🚜 RÉGLAGE DES 2 MISSIONS")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**BOT 1 (Haut)**")
        p1_in = st.number_input("ACHAT 1", value=1.3600, format="%.4f")
        p1_out = st.number_input("VENTE 1", value=1.3800, format="%.4f")
    
    with col_b:
        st.markdown("**BOT 2 (Bas)**")
        p2_in = st.number_input("ACHAT 2", value=1.3400, format="%.4f")
        p2_out = st.number_input("VENTE 2", value=1.3800, format="%.4f") # Tu peux changer ici !

    # Calcul Volume (50/50 du solde)
    vol_par_bot = (usdc_reel * 0.96 / 2) / prix_actuel if usdc_reel > 28 else 0

    if st.button("🚀 LANCER LES 2 SNIPERS"):
        if vol_par_bot < 10:
            st.error("Solde trop petit (Besoin de 28$ min pour 2 bots)")
        else:
            # Ordre 1
            params1 = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p1_out}}
            kraken.create_limit_buy_order('XRP/USDC', vol_par_bot, p1_in, params1)
            time.sleep(0.5)
            # Ordre 2
            params2 = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p2_out}}
            kraken.create_limit_buy_order('XRP/USDC', vol_par_bot, p2_in, params2)
            
            st.balloons()
            st.success(f"✅ 2 ordres placés ({vol_par_bot:.1f} XRP chacun)")

    if st.button("🚨 ANNULER TOUT"):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Liaison : {e}")

time.sleep(30)
st.rerun()
