import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM
st.set_page_config(page_title="XRP Sniper Duo", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] { color: #007AFF !important; font-size: 2.2rem !important; }
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] { color: #FF9500 !important; font-size: 2.2rem !important; }
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 25px; padding: 20px; text-align: center; color: white; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 60px; border-radius: 20px !important; background-color: #F3BA2F !important; font-weight: bold; font-size: 18px !important; }
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

    # --- CONFIGURATION MANUELLE ---
    st.markdown("### 🚜 RÉGLAGE DES 2 MISSIONS")
    
    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown("**BOT 1**")
        p1_in = st.number_input("ACHAT 1", value=1.3600, format="%.4f", key="p1i")
        p1_out = st.number_input("VENTE 1", value=1.3800, format="%.4f", key="p1o")
    
    with c_b:
        st.markdown("**BOT 2**")
        p2_in = st.number_input("ACHAT 2", value=1.3400, format="%.4f", key="p2i")
        p2_out = st.number_input("VENTE 2", value=1.3800, format="%.4f", key="p2o")

    # --- BOUTONS SÉPARÉS ---
    st.write("")
    l1, l2 = st.columns(2)

    # Sécurité : On utilise 48% du solde pour chaque bot pour être sûr de passer
    vol_test = (usdc_reel * 0.48) / prix_actuel if usdc_reel > 14 else 0

    with l1:
        if st.button("🚀 LANCER BOT 1"):
            if usdc_reel > 14:
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p1_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol_test, p1_in, params)
                st.success(f"✅ Bot 1 actif ({vol_test:.1f} XRP)")
                st.balloons()
            else: st.error("Solde < 14$")

    with l2:
        if st.button("🚀 LANCER BOT 2"):
            if usdc_reel > 14:
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p2_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol_test, p2_in, params)
                st.success(f"✅ Bot 2 actif ({vol_test:.1f} XRP)")
                st.balloons()
            else: st.error("Solde < 14$")

    if st.button("🚨 ANNULER TOUT / RESET"):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Liaison : {e}")

time.sleep(30)
st.rerun()
