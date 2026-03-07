import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES ORDRES LANCÉS
if 'order_ids' not in st.session_state: st.session_state.order_ids = {1: None, 2: None, 3: None}
if 'profit_reel' not in st.session_state: st.session_state.profit_reel = 0.0
if 'last_click' not in st.session_state: st.session_state.last_click = 0

st.set_page_config(page_title="XRP Sniper Pro", layout="centered")
st.markdown("<style>.stApp { background: #F8F9FA; } .profit-box { background: #28a745; color: white; padding: 15px; border-radius: 20px; text-align: center; margin-bottom: 10px; } .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }</style>", unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    st.markdown(f'<div class="profit-box">PROFIT RÉEL : + {st.session_state.profit_reel:.2f} $</div>', unsafe_allow_html=True)
    st.write(f"### 🔵 LIBRE : {usdc_dispo:.2f} $ | 📈 PRIX : {prix_actuel:.4f} $")

    prices_in = [1.3650, 1.3400, 1.3200]

    for i in range(3):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # VÉRIFICATION : L'ordre de ce bot est-il toujours vivant chez Kraken ?
        bot_ordre_id = st.session_state.order_ids[p_idx]
        mission_active = any(o['id'] == bot_ordre_id for o in orders) if bot_ordre_id else False
        
        # Si on ne trouve pas l'ID, on cherche par le prix exact (sécurité)
        if not mission_active:
            for o in orders:
                if abs(float(o['price']) - p_base) < 0.0001:
                    mission_active = True
                    st.session_state.order_ids[p_idx] = o['id']
                    break

        status_txt = "🟢 ACTIF" if mission_active else "⚪ INACTIF"
        montant_label = ""
        if mission_active:
            for o in orders:
                if o['id'] == st.session_state.order_ids[p_idx]:
                    montant_label = f" | 📦 {float(o['amount']) * float(o['price']):.2f} $"

        with st.expander(f"🚜 BOT {p_idx} | {status_txt}{montant_label}", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            m_invest = st.number_input("MONTANT $", value=16.0, min_value=14.0, key=f"m{i}")
            p_in = st.number_input("ACHAT", value=p_base, format="%.4f", key=f"in{i}")
            p_out = st.number_input("VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            col_l, col_s = st.columns(2)
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if time.time() - st.session_state.last_click > 5 and usdc_dispo >= m_invest:
                    st.session_state.last_click = time.time()
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    new_order = kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.session_state.order_ids[p_idx] = new_order['id'] # ON MÉMORISE L'ID
                    st.success("Ordre envoyé !")
                    time.sleep(2)
                    st.rerun()

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                for o in orders:
                    if o['id'] == st.session_state.order_ids[p_idx] or abs(float(o['price']) - p_in) < 0.0001:
                        kraken.cancel_order(o['id'])
                st.session_state.order_ids[p_idx] = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📦 MISSIONS RÉELLES")
    for o in orders:
        ico = "🎯" if o['side'] == 'buy' else "💰"
        st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
