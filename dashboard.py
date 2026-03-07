import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES ÉTATS
if 'bot_active' not in st.session_state:
    st.session_state.bot_active = {1: False, 2: False, 3: False, 4: False}
if 'cycles' not in st.session_state: st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0

st.set_page_config(page_title="XRP Sniper Libre", layout="centered")

try:
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    st.write(f"### 💰 PROFIT : {st.session_state.profit_total:.2f} $ | 🔵 LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # DÉTECTION RÉELLE
        is_running = st.session_state.bot_active[p_idx]
        mission_active = any(abs(float(o['price']) - p_base) < 0.05 for o in orders)
        status = "🟢 ACTIF" if is_running else "⚪ INACTIF"
        
        with st.expander(f"🚜 BOT {p_idx} | {status} | 🔄 {st.session_state.cycles[p_idx]} Cycles"):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            
            # --- ICI : CASE VENTE LIBRE ---
            p_out = st.number_input(f"VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # BOULE DE NEIGE (Seulement si is_running est ON)
            if is_running and not mission_active and usdc_dispo >= m_invest:
                st.session_state.profit_total += (p_out - p_in) * (m_invest / p_in)
                st.session_state.cycles[p_idx] += 1
                vol = round(m_invest / p_in, 1)
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            col_l, col_s = st.columns(2)
            
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                st.session_state.bot_active[p_idx] = True
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                st.session_state.bot_active[p_idx] = False
                for o in orders:
                    p_o = float(o['price'])
                    if abs(p_o - p_in) < 0.05 or abs(p_o - p_out) < 0.05:
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
