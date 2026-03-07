import streamlit as st
import ccxt
import time

# 1. STYLE PRO
st.set_page_config(page_title="XRP Auto-Sniper", layout="wide")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] { color: #007AFF !important; }
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] { color: #FF9500 !important; }
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 20px; padding: 15px; text-align: center; color: white; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; }
    </style>
    """, unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    
    # SCAN DU SOLDE EN TEMPS RÉEL
    balance = kraken.fetch_balance()
    usdc_reel = balance['total'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # AFFICHAGE
    st.markdown(f'<div class="cumul-box"><h1>SOLDE TOTAL : {usdc_reel:.2f} $</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("DISPO USDC", f"{usdc_reel:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # --- LOGIQUE AUTO-SCAN ---
    # Le bot divise par 3 ton solde actuel (donc s'il y a +10$, il les voit !)
    vol_auto = (usdc_reel * 0.96 / 3) / prix_actuel

    cols = st.columns(3)
    for i in range(3):
        with cols[i]:
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            st.subheader(f"🚜 BOT {i+1}")
            p_in = st.number_input(f"ACHAT {i+1}", value=1.36 - (i*0.02), format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE {i+1}", value=p_in + 0.02, format="%.4f", key=f"out{i}")
            
            if st.button(f"🚀 LANCER B{i+1}", key=f"btn{i}"):
                if vol_auto >= 10:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_auto, p_in, params)
                    st.success(f"B{i+1} Lancé avec {vol_auto:.1f} XRP")
                else:
                    st.error(f"Besoin de 14$ min (Actuel: {vol_auto*prix_actuel:.1f}$)")
            st.markdown("</div>", unsafe_allow_html=True)

    # MISSIONS EN DIRECT
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES SUR KRAKEN")
    orders = kraken.fetch_open_orders('XRP/USDC')
    for o in orders:
        st.info(f"🎯 {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

    if st.button("🚨 ANNULER TOUT & RECHARGER"):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(20) # Scan toutes les 20 secondes
st.rerun()
