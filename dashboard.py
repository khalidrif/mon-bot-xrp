import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM
st.set_page_config(page_title="XRP Sniper Pro", layout="wide")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] { color: #007AFF !important; }
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] { color: #FF9500 !important; }
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 20px; padding: 15px; text-align: center; color: white; margin-bottom: 10px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION ANTI-BLOCAGE
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    
    balance = kraken.fetch_balance()
    usdc_total = balance['total'].get('USDC', 0.0)
    usdc_dispo = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # HEADER SCANNER
    st.markdown(f'<div class="cumul-box"><p style="margin:0; opacity:0.8;">SOLDE TOTAL KRAKEN (SCAN)</p><h1>{usdc_total:.2f} $</h1></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("LIBRE (POUR BOTS)", f"{usdc_dispo:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. INTERFACE 3 BOTS AVEC STOP INDIVIDUEL
    cols = st.columns(3)
    prices_in = [1.3600, 1.3400, 1.3200]
    
    # Calcul volume basé sur le solde total divisé par 3
    vol_auto = (usdc_total * 0.95 / 3) / prix_actuel

    for i in range(3):
        p_idx = i + 1
        with cols[i]:
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            st.subheader(f"🚜 B{p_idx}")
            p_in = st.number_input(f"ACHAT", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE", value=p_in + 0.02, format="%.4f", key=f"out{i}")
            
            # BOUTONS LANCER / STOP
            if st.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo > 13.5:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_auto, p_in, params)
                    st.success(f"B{p_idx} OK")
                    st.balloons()
                else: st.error("Solde Libre < 14$")
            
            if st.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                orders = kraken.fetch_open_orders('XRP/USDC')
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # 4. MISSIONS
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES")
    orders = kraken.fetch_open_orders('XRP/USDC')
    if orders:
        for o in orders:
            st.info(f"🎯 {o['side'].upper()} {o['amount']:.1f} XRP @ {o['price']} $")
    else: st.write("Aucun ordre actif.")

    if st.button("🚨 RESET TOTAL", use_container_width=True):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"⚠️ Erreur : {e}")
    st.info("Attends 1 min (Rate Limit).")

# SCAN TOUTES LES 60 SECONDES
time.sleep(60)
st.rerun()
