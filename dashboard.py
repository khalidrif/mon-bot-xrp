import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DU PROFIT
if 'profit_reel' not in st.session_state:
    st.session_state.profit_reel = 0.0

# STYLE PREMIUM
st.set_page_config(page_title="XRP Sniper Pro", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .profit-box { background: #28a745; color: white; padding: 20px; border-radius: 25px; text-align: center; margin-bottom: 10px; }
    .status-box { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 15px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; height: 45px; }
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

    # AFFICHAGE PROFIT & CAPITAL
    st.markdown(f'<div class="profit-box"><p style="margin:0; opacity:0.9;">PROFIT RÉEL ENCAISSÉ</p><h1>+ {st.session_state.profit_reel:.2f} $</h1></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box"><p style="margin:0; color:grey;">CAPITAL TOTAL KRAKEN</p><h2>{usdc_total:.2f} $</h2></div>', unsafe_allow_html=True)
    
    c_a, c_b = st.columns(2)
    c_a.metric("LIBRE (SCAN)", f"{usdc_dispo:.2f} $")
    c_b.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. LOGIQUE D'INJECTION AUTOMATIQUE (TES 17$)
    prices_in = [1.3600, 1.3400, 1.3200]
    if usdc_dispo > 14.0:
        cible = max(prices_in)
        vol = round((usdc_dispo * 0.95) / cible, 1)
        if st.button(f"⚡ INJECTER {usdc_dispo:.2f}$ SUR {cible}$", use_container_width=True):
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': round(cible + 0.02, 4)}}
            kraken.create_limit_buy_order('XRP/USDC', vol, round(cible, 4), params)
            st.balloons()
            st.rerun()

    # 4. LES 3 BOITES AVEC STOP INDIVIDUEL
    for i in range(3):
        p_idx = i + 1
        with st.expander(f"🚜 BOT {p_idx} - RÉGLAGES", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            p_in = st.number_input(f"ACHAT", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")
            
            col_l, col_s = st.columns(2)
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                vol_auto = round((usdc_dispo * 0.95) / p_in, 1)
                if vol_auto >= 10:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_auto, p_in, params)
                    st.success("OK")
                else: st.error("Solde < 14$")
            
            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                orders = kraken.fetch_open_orders('XRP/USDC')
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # 5. MISSIONS ACTIVES
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES")
    orders = kraken.fetch_open_orders('XRP/USDC')
    if orders:
        for o in orders:
            couleur = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{couleur} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

    if st.button("🚨 RESET COMPTEUR PROFIT"):
        st.session_state.profit_reel = 0.0
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
