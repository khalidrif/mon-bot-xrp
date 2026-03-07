import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM
st.set_page_config(page_title="XRP Multi-Sniper", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] { color: #007AFF !important; font-size: 2rem !important; }
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] { color: #FF9500 !important; font-size: 2rem !important; }
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 25px; padding: 20px; text-align: center; color: white; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
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

    # --- INTERFACE 3 COLONNES ---
    c1, c2, c3 = st.columns(3)

    # BOT 1
    with c1:
        st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
        st.subheader("🚜 B1")
        p1_i = st.number_input("ACHAT 1", value=1.3600, format="%.4f", key="p1i")
        p1_o = st.number_input("VENTE 1", value=1.3800, format="%.4f", key="p1o")
        if st.button("🚀 LANCER", key="run1"):
            vol = (usdc_reel * 0.95 / 2) / prix_actuel
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p1_o}}
            kraken.create_limit_buy_order('XRP/USDC', vol, p1_i, params)
            st.success("B1 OK")
        if st.button("🗑️ STOP", key="stop1"):
            orders = kraken.fetch_open_orders('XRP/USDC')
            for o in orders:
                if float(o['price']) == p1_i: kraken.cancel_order(o['id'])
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # BOT 2
    with c2:
        st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
        st.subheader("🚜 B2")
        p2_i = st.number_input("ACHAT 2", value=1.3400, format="%.4f", key="p2i")
        p2_o = st.number_input("VENTE 2", value=1.3600, format="%.4f", key="p2o")
        if st.button("🚀 LANCER", key="run2"):
            vol = (usdc_reel * 0.95 / 2) / prix_actuel
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p2_o}}
            kraken.create_limit_buy_order('XRP/USDC', vol, p2_i, params)
            st.success("B2 OK")
        if st.button("🗑️ STOP", key="stop2"):
            orders = kraken.fetch_open_orders('XRP/USDC')
            for o in orders:
                if float(o['price']) == p2_i: kraken.cancel_order(o['id'])
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # BOT 3
    with c3:
        st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
        st.subheader("🚜 B3")
        p3_i = st.number_input("ACHAT 3", value=1.3200, format="%.4f", key="p3i")
        p3_o = st.number_input("VENTE 3", value=1.3400, format="%.4f", key="p3o")
        if st.button("🚀 LANCER", key="run3"):
            vol = (usdc_reel * 0.95 / 3) / prix_actuel
            kraken.create_limit_buy_order('XRP/USDC', vol, p3_i)
            st.success("B3 OK")
        if st.button("🗑️ STOP", key="stop3"):
            orders = kraken.fetch_open_orders('XRP/USDC')
            for o in orders:
                if float(o['price']) == p3_i: kraken.cancel_order(o['id'])
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # MISSIONS
    st.divider()
    st.markdown("### 📦 MISSIONS EN COURS")
    open_orders = kraken.fetch_open_orders('XRP/USDC')
    if open_orders:
        for order in open_orders:
            st.info(f"🎯 {order['side'].upper()} {order['amount']} XRP @ {order['price']} $")
    else: st.write("Aucune mission active.")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(30)
st.rerun()
