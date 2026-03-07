import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM (Duo Interface)
st.set_page_config(page_title="XRP Duo Sniper", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    
    /* Couleurs Métriques */
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] { color: #007AFF !important; font-size: 2.2rem !important; }
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] { color: #FF9500 !important; font-size: 2.2rem !important; }
    
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 25px; padding: 20px; text-align: center; color: white; margin-bottom: 20px; box-shadow: 0px 10px 20px rgba(40, 167, 69, 0.1); }
    .stButton>button { width: 100%; height: 60px; border-radius: 20px !important; background-color: #F3BA2F !important; font-weight: bold; color: black !important; }
    .bot-card { background: white; padding: 20px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.03); }
    </style>
    """, unsafe_allow_html=True)

if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0
st.markdown(f'<div class="cumul-box"><p style="margin:0; opacity:0.8;">PROFIT CUMULÉ</p><h1>+ {st.session_state.profit_total:.2f} $</h1></div>', unsafe_allow_html=True)

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

    # --- CALCUL VOLUME SÉCURISÉ (48% par clic) ---
    vol_clic = (usdc_reel * 0.48) / prix_actuel if usdc_reel > 14 else 10.5

    # --- INTERFACE DUO ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
        st.subheader("🚜 BOT 1")
        p1_in = st.number_input("ACHAT 1", value=1.3600, format="%.4f", key="p1i")
        p1_out = st.number_input("VENTE 1", value=1.3800, format="%.4f", key="p1o")
        if st.button("🚀 LANCER B1"):
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p1_out}}
            kraken.create_limit_buy_order('XRP/USDC', vol_clic, p1_in, params)
            st.balloons()
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
        st.subheader("🚜 BOT 2")
        p2_in = st.number_input("ACHAT 2", value=1.3400, format="%.4f", key="p2i")
        p2_out = st.number_input("VENTE 2", value=1.3800, format="%.4f", key="p2o")
        if st.button("🚀 LANCER B2"):
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p2_out}}
            kraken.create_limit_buy_order('XRP/USDC', vol_clic, p2_in, params)
            st.balloons()
        st.markdown("</div>", unsafe_allow_html=True)
            with c3:
        st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
        st.subheader("🚜 BOT 3")
        # On utilise des 'key' uniques (p3i, p3o)
        p3_in = st.number_input("ACHAT 3", value=1.3200, format="%.4f", key="p3i")
        p3_out = st.number_input("VENTE 3", value=1.3400, format="%.4f", key="p3o")
        
        if st.button("🚀 LANCER B3"):
            # Calcul : on prend 1/3 de ton argent disponible
            vol_b3 = (usdc_reel * 0.95 / 3) / prix_actuel
            if vol_b3 >= 10:
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p3_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol_b3, p3_in, params)
                st.balloons()
                st.success("B3 activé !")
            else:
                st.error("Solde insuffisant (Attends ton dépôt !)")
        st.markdown("</div>", unsafe_allow_html=True)


    # --- MISSIONS EN COURS ---
    st.divider()
    st.markdown("### 📦 MISSIONS EN COURS")
    open_orders = kraken.fetch_open_orders('XRP/USDC')
    if open_orders:
        for order in open_orders:
            st.info(f"🎯 {order['side'].upper()} {order['amount']} XRP @ {order['price']} $")
    else:
        st.write("Aucune mission active.")

    if st.button("🚨 ANNULER TOUT / RESET"):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Liaison : {e}")

time.sleep(30)
st.rerun()
