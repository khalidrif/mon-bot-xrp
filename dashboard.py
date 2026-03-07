import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES ÉTATS (VERROU DE SÉCURITÉ)
if 'bot_on' not in st.session_state: st.session_state.bot_on = {1:False, 2:False, 3:False, 4:False}
if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0
if 'cycles' not in st.session_state: st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}

st.set_page_config(page_title="XRP Sniper Discipliné", layout="centered")

try:
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True, 'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    orders = kraken.fetch_open_orders('XRP/USDC')
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)

    st.write(f"### 💰 PROFIT : {st.session_state.profit_total:.2f} $ | 🔵 LIBRE : {usdc_dispo:.2f} $")

    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # DÉTECTION RÉELLE
        mission_active = any(abs(float(o['price']) - p_base) < 0.02 or abs(float(o['price']) - (p_base + 0.02)) < 0.02 for o in orders)
        status = "🟢 ACTIF" if mission_active else "⚪ INACTIF"
        
        with st.expander(f"🚜 BOT {p_idx} | {status} | 🔄 {st.session_state.cycles[p_idx]} Cycles"):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = round(p_in + 0.02, 4)

            # --- LA BOULE DE NEIGE DISCIPLINÉE ---
            # Il ne relance QUE SI l'interrupteur 'bot_on' est VRAI
            if st.session_state.bot_on[p_idx] and not mission_active and usdc_dispo >= m_invest:
                st.session_state.profit_total += (p_out - p_in) * (m_invest / p_in)
                st.session_state.cycles[p_idx] += 1
                vol = round(m_invest / p_in, 1)
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            col_l, col_s = st.columns(2)
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                st.session_state.bot_on[p_idx] = True # ON ALLUME L'INTERRUPTEUR
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                st.session_state.bot_on[p_idx] = False # ON COUPE L'INTERRUPTEUR (SÉCURITÉ)
                for o in orders:
                    if abs(float(o['price']) - p_in) < 0.05 or abs(float(o['price']) - p_out) < 0.05:
                        kraken.cancel_order(o['id'])
                st.rerun()

    # MISSIONS RÉELLES
    st.divider()
    for o in orders:
        ico = "🎯" if o['side'] == 'buy' else "💰"
        st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
