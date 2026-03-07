import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM
st.set_page_config(page_title="XRP Sniper Profit", layout="wide")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] { color: #007AFF !important; }
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] { color: #FF9500 !important; }
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 20px; padding: 15px; text-align: center; color: white; margin-bottom: 10px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .profit-text { color: #28a745; font-weight: bold; font-size: 0.9rem; text-align: center; margin-top: 5px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION KRAKEN
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_total = balance['total'].get('USDC', 0.0)
    usdc_dispo = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # HEADER SCANNER
    st.markdown(f'<div class="cumul-box"><p style="margin:0; opacity:0.8;">SOLDE TOTAL KRAKEN</p><h1>{usdc_total:.2f} $</h1></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("DISPO (POUR BOTS)", f"{usdc_dispo:.2f} $")
    c2.metric("PRIX XRP LIVE", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. INTERFACE 3 BOTS AVEC PROFIT NET
    cols = st.columns(3)
    prices_in = [1.3600, 1.3400, 1.3200]
    vol_auto = (usdc_total * 0.95 / 3) / prix_actuel # Puissance de feu par bot

    for i in range(3):
        p_idx = i + 1
        with cols[i]:
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            st.subheader(f"🚜 B{p_idx}")
            p_in = st.number_input(f"ACHAT", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE", value=p_in + 0.02, format="%.4f", key=f"out{i}")
            
            # --- CALCUL DU PROFIT NET (Après frais 0.26%) ---
            gain_brut = vol_auto * (p_out - p_in)
            frais_estimes = (vol_auto * p_in * 0.0026) + (vol_auto * p_out * 0.0026)
            profit_net = gain_brut - frais_estimes
            
            st.markdown(f"<p class='profit-text'>📈 Profit Net : +{profit_net:.2f} $</p>", unsafe_allow_html=True)
            
            if st.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo > 13.5:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_auto, p_in, params)
                    st.success("Lancé !")
                    st.balloons()
                else: st.error("Solde < 14$")
            
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

time.sleep(60)
st.rerun()
