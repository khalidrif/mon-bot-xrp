import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES PROFITS, CYCLES ET ÉTATS
if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0
if 'cycles' not in st.session_state: st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
if 'bot_active' not in st.session_state: st.session_state.bot_active = {1:False, 2:False, 3:False, 4:False}
if 'last_click' not in st.session_state: st.session_state.last_click = 0

st.set_page_config(page_title="XRP Sniper Discipliné", layout="centered")

try:
    # 2. CONNEXION KRAKEN (FIX NONCE)
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

    # HEADER
    st.write(f"### 💰 PROFIT : {st.session_state.profit_total:.2f} $ | 🔵 LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    # LES 4 PRIX CIBLES
    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # DÉTECTION PAR ZONE (B1:>1.35, B2:1.33-1.35, B3:1.31-1.33, B4:<1.31)
        mission_active = False
        for o in orders:
            p_o = float(o['price'])
            if (i == 0 and p_o > 1.35) or (i == 1 and 1.33 <= p_o <= 1.35) or \
               (i == 2 and 1.31 <= p_o < 1.33) or (i == 3 and p_o < 1.31):
                mission_active = True
                break

        is_running = st.session_state.bot_active[p_idx]
        status = "🟢 ACTIF" if mission_active else "⚪ INACTIF"
        
        with st.expander(f"🚜 BOT {p_idx} | {status} | 🔄 {st.session_state.cycles[p_idx]} Cycles"):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = round(p_in + 0.02, 4)

            # --- LA BOULE DE NEIGE DISCIPLINÉE (NE RELANCE PAS SI STOP) ---
            if is_running and not mission_active and usdc_dispo >= m_invest:
                # On valide le profit réel seulement si le bot est encore sur ON
                st.session_state.profit_total += (p_out - p_in) * (m_invest / p_in)
                st.session_state.cycles[p_idx] += 1
                # Relance automatique
                vol = round(m_invest / p_in, 1)
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            col_l, col_s = st.columns(2)
            
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if time.time() - st.session_state.last_click > 5 and usdc_dispo >= m_invest:
                    st.session_state.last_click = time.time()
                    st.session_state.bot_active[p_idx] = True # MÉMOIRE SUR ON
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                st.session_state.bot_active[p_idx] = False # MÉMOIRE SUR OFF (Prioritaire)
                for o in orders:
                    p_o = float(o['price'])
                    if (i == 0 and p_o > 1.35) or (i == 1 and 1.33 <= p_o <= 1.35) or \
                       (i == 2 and 1.31 <= p_o < 1.33) or (i == 3 and p_o < 1.31):
                        kraken.cancel_order(o['id'])
                st.rerun()

    # MISSIONS RÉELLES
    st.divider()
    for o in orders:
        ico = "🎯" if o['side'] == 'buy' else "💰"
        st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

    # BOUTON DE NETTOYAGE
    if st.button("🚨 RESET TOUS LES COMPTEURS"):
        st.session_state.profit_total = 0.0
        st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
