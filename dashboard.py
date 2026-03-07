import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DU PROFIT RÉEL
if 'profit_reel' not in st.session_state:
    st.session_state.profit_reel = 0.0

st.set_page_config(page_title="XRP Sniper Custom", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); }
    .profit-box { background: #28a745; color: white; padding: 15px; border-radius: 20px; text-align: center; margin-bottom: 10px; }
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

    # AFFICHAGE
    st.markdown(f'<div class="profit-box">PROFIT RÉEL : + {st.session_state.profit_reel:.2f} $</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box"><p style="margin:0; color:grey;">CAPITAL TOTAL</p><h2>{usdc_total:.2f} $</h2></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("LIBRE (USDC)", f"{usdc_dispo:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. INTERFACE 3 BOTS AVEC MONTANT MANUEL
    orders = kraken.fetch_open_orders('XRP/USDC')
    prices_in = [1.3600, 1.3400, 1.3200]

    for i in range(3):
        p_idx = i + 1
        # On cherche si un ordre existe pour ce prix
        montant_actuel = 0.0
        for o in orders:
            if float(o['price']) == prices_in[i]:
                montant_actuel = float(o['amount']) * float(o['price'])
        
        status = f" | 📦 {montant_actuel:.2f} $" if montant_actuel > 0 else " | 😴 Inactif"
        
        with st.expander(f"🚜 BOT {p_idx}{status}", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            
            # --- LES RÉGLAGES ---
            m_invest = st.number_input("MONTANT À INVESTIR ($)", value=15.0, min_value=0.0, step=1.0, key=f"m{i}")
            p_in = st.number_input("PRIX ACHAT", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input("PRIX VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")
            
            col_l, col_s = st.columns(2)
            
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo >= m_invest and m_invest >= 14.0:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success(f"B{p_idx} lancé avec {m_invest}$")
                    st.rerun()
                elif m_invest < 14.0:
                    st.error("Minimum 14$ requis")
                else:
                    st.error("Solde insuffisant")
            
            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # MISSIONS
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES")
    if orders:
        for o in orders:
            ico = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

    if st.button("🚨 RESET TOTAL", use_container_width=True):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
