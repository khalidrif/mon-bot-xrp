import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM (Fond Soft Grey)
st.set_page_config(page_title="XRP Double Grid", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] { color: #007AFF !important; font-size: 2.2rem !important; }
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] { color: #FF9500 !important; font-size: 2.2rem !important; }
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 25px; padding: 20px; text-align: center; color: white; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 65px; border-radius: 20px !important; background-color: #F3BA2F !important; font-weight: bold; font-size: 20px !important; }
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

    # --- CONFIGURATION DOUBLE PALIER ---
    st.markdown("### 🪜 ESCALIER DE 2 BOTS")
    p1 = st.number_input("PRIX BOT 1 (Haut)", value=1.3600, format="%.4f")
    p2 = st.number_input("PRIX BOT 2 (Bas)", value=1.3400, format="%.4f")
    gap_vente = st.number_input("GAIN PAR VENTE ($)", value=0.0200, format="%.4f")

    # Calcul : 39$ / 2 = 19.50$ (soit env 14 XRP)
    vol_par_bot = (usdc_reel * 0.96 / 2) / p1 if usdc_reel > 28 else 0

    if st.button("🚀 DÉPLOYER LES 2 BOTS"):
        if vol_par_bot < 10:
            st.error("Solde trop petit pour 2 bots (Min 28 USDC requis)")
        else:
            # BOT 1
            params1 = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p1 + gap_vente}}
            kraken.create_limit_buy_order('XRP/USDC', vol_par_bot, p1, params1)
            time.sleep(0.5)
            # BOT 2
            params2 = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p2 + gap_vente}}
            kraken.create_limit_buy_order('XRP/USDC', vol_par_bot, p2, params2)
            
            st.balloons()
            st.success(f"✅ 2 Bots lancés ({vol_par_bot:.1f} XRP chacun)")

    if st.button("🚨 ANNULER TOUT / RESET"):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Liaison : {e}")

time.sleep(30)
st.rerun()
