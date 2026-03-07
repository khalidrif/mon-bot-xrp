import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES PROFITS ET ÉTATS
if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0
if 'cycles' not in st.session_state: st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
if 'bot_active' not in st.session_state: st.session_state.bot_active = {1:False, 2:False, 3:False, 4:False}

st.set_page_config(page_title="XRP Auto-Snowball", layout="centered")

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

    # 3. LES 4 BOTS EN MODE "REACHAT AUTO"
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

        status = "🟢 ACTIF" if mission_active else "⚪ INACTIF"
        
        with st.expander(f"🚜 BOT {p_idx} | {status} | 🔄 {st.session_state.cycles[p_idx]} Cycles"):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = round(p_in + 0.02, 4)

            # --- LA BOULE DE NEIGE AUTOMATIQUE ---
            if st.session_state.bot_active[p_idx] and not mission_active and usdc_dispo >= m_invest:
                # 1. Calcul et ajout du profit
                gain = (p_out - p_in) * (m_invest / p_in)
                st.session_state.profit_total += gain
                st.session_state.cycles[p_idx] += 1
                
                # 2. RELANCE DE L'ACHAT AUTOMATIQUE ( Snowball )
                vol = round(m_invest / p_in, 1)
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            col_l, col_s = st.columns(2)
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    st.session_state.bot_active[p_idx] = True
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                st.session_state.bot_active[p_idx] = False
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

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
