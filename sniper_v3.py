import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES PROFITS ET ÉTATS
if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0
if 'bot_profits' not in st.session_state: st.session_state.bot_profits = {1:0.0, 2:0.0, 3:0.0, 4:0.0}
if 'cycles' not in st.session_state: st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
if 'bot_active' not in st.session_state: st.session_state.bot_active = {1:False, 2:False, 3:False, 4:False}

st.set_page_config(page_title="XRP SNIPER PRO", layout="centered")

try:
    # 2. CONNEXION KRAKEN
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    # HEADER GÉANT
    st.write(f"## 💵 PROFIT : {st.session_state.profit_total:.4f} $")
    st.write(f"### 🔵 LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    # CONFIGURATION DES 4 BOTS (VOLUMES UNIQUES)
    bot_configs = {
        1: {"p": 1.3650, "v": 10.6},
        2: {"p": 1.3400, "v": 10.8},
        3: {"p": 1.3200, "v": 11.0},
        4: {"p": 1.3000, "v": 11.2}
    }

    for p_idx, cfg in bot_configs.items():
        # DÉTECTION PRÉCISE
        mission_active = False
        montant_reel = 0.0
        for o in orders:
            if abs(float(o['amount']) - cfg['v']) < 0.01:
                mission_active = True
                montant_reel = float(o['amount']) * float(o['price'])
                break

        # --- LOGIQUE BOULE DE NEIGE ---
        if st.session_state.bot_active[p_idx] and not mission_active and usdc_dispo >= (cfg['p'] * cfg['v']):
            gain_net = (0.02) * cfg['v']
            st.session_state.profit_total += gain_net
            st.session_state.bot_profits[p_idx] += gain_net
            st.session_state.cycles[p_idx] += 1
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': cfg['p'] + 0.02}}
            kraken.create_limit_buy_order('XRP/USDC', cfg['v'], cfg['p'], params)
            st.rerun()

        # --- TITRE GÉANT POUR IPHONE ---
        status = "🟢" if mission_active else "⚪"
        p_bot = st.session_state.bot_profits[p_idx]
        # Format : VOYANT | MONTANT | BOT | CYCLES | PROFIT
        titre = f"{status} {montant_reel:.2f}$ | BOT {p_idx} | 🔄 {st.session_state.cycles[p_idx]} | 💰 +{p_bot:.4f}"

        with st.expander(titre, expanded=(p_idx==1)):
            c1, c2 = st.columns(2)
            if c1.button(f"🚀 LANCER B{p_idx}", key=f"run{p_idx}"):
                st.session_state.bot_active[p_idx] = True
                if usdc_dispo >= (cfg['p'] * cfg['v']):
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': cfg['p'] + 0.02}}
                    kraken.create_limit_buy_order('XRP/USDC', cfg['v'], cfg['p'], params)
                    st.rerun()

            if c2.button(f"🗑️ STOP B{p_idx}", key=f"stop{p_idx}"):
                st.session_state.bot_active[p_idx] = False
                for o in orders:
                    if abs(float(o['amount']) - cfg['v']) < 0.01:
                        kraken.cancel_order(o['id'])
                st.rerun()

    # MISSIONS RÉELLES
    st.divider()
    for o in orders:
        ico = "🎯 BUY" if o['side'] == 'buy' else "💰 SELL"
        st.info(f"**{ico} {o['amount']} XRP @ {o['price']} $**")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
