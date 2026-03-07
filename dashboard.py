import streamlit as st
import ccxt
import time

# 1. FORCER LA MÉMOIRE (DOUBLE SERRURE)
if 'bot_active' not in st.session_state:
    st.session_state.bot_active = {1: False, 2: False, 3: False, 4: False}
if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0
if 'cycles' not in st.session_state: st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}

st.set_page_config(page_title="XRP Sniper STOP Force", layout="centered")

try:
    # 2. CONNEXION KRAKEN
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    st.write(f"### 💰 PROFIT : {st.session_state.profit_total:.2f} $ | 🔵 LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # ON VÉRIFIE SI UN ORDRE EXISTE RÉELLEMENT
        mission_active = False
        for o in orders:
            p_o = float(o['price'])
            if abs(p_o - p_base) < 0.05 or abs(p_o - (p_base + 0.02)) < 0.05:
                mission_active = True
                break

        # --- LA SERRURE ---
        # Si l'utilisateur a dit STOP, on ignore TOUT le reste.
        is_running = st.session_state.bot_active[p_idx]
        status = "🟢 ACTIF" if mission_active else "⚪ INACTIF"
        
        with st.expander(f"🚜 BOT {p_idx} | {status} | 🔄 {st.session_state.cycles[p_idx]} Cycles"):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = round(p_in + 0.02, 4)

            # --- BOULE DE NEIGE DISCIPLINÉE ---
            # SEULEMENT si is_running est VRAI et qu'il n'y a plus d'ordre
            if is_running and not mission_active and usdc_dispo >= m_invest:
                st.session_state.profit_total += (p_out - p_in) * (m_invest / p_in)
                st.session_state.cycles[p_idx] += 1
                vol = round(m_invest / p_in, 1)
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            col_l, col_s = st.columns(2)
            
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                st.session_state.bot_active[p_idx] = True # ON VERROUILLE SUR ON
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                st.session_state.bot_active[p_idx] = False # ON VERROUILLE SUR OFF
                # On nettoie Kraken
                for o in orders:
                    p_o = float(o['price'])
                    if abs(p_o - p_base) < 0.05 or abs(p_o - (p_base + 0.02)) < 0.05:
                        kraken.cancel_order(o['id'])
                st.write("ARRÊTÉ. Patientez...")
                time.sleep(2)
                st.rerun()

    st.divider()
    if st.button("🚨 RESET TOTAL (A0)"):
        st.session_state.bot_active = {1:False, 2:False, 3:False, 4:False}
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
