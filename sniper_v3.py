import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES PROFITS ET ÉTATS (RÉSISTE AU RECHARGEMENT)
if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0
if 'bot_profits' not in st.session_state: st.session_state.bot_profits = {1:0.0, 2:0.0, 3:0.0, 4:0.0}
if 'cycles' not in st.session_state: st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
if 'bot_active' not in st.session_state: st.session_state.bot_active = {1:False, 2:False, 3:False, 4:False}

st.set_page_config(page_title="XRP Sniper Master V3", layout="centered")

try:
    # 2. CONNEXION KRAKEN (TES NOUVEAUX SECRETS)
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    # HEADER GÉNÉRAL
    st.write(f"### 💰 PROFIT TOTAL : {st.session_state.profit_total:.4f} $ | 🔵 LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    # CONFIGURATION UNIQUE PAR BOT (EMPREINTE DIGITALE PAR VOLUME)
    bot_configs = {
        1: {"p": 1.3650, "v": 10.6},
        2: {"p": 1.3400, "v": 10.8},
        3: {"p": 1.3200, "v": 11.0},
        4: {"p": 1.3000, "v": 11.2}
    }

    for p_idx, cfg in bot_configs.items():
        # DÉTECTION PRÉCISE PAR VOLUME
        mission_active = False
        montant_reel = 0.0
        for o in orders:
            if abs(float(o['amount']) - cfg['v']) < 0.01:
                mission_active = True
                montant_reel = float(o['amount']) * float(o['price'])
                break

        # --- LOGIQUE BOULE DE NEIGE AUTOMATIQUE ---
        is_running = st.session_state.bot_active[p_idx]
        if is_running and not mission_active and usdc_dispo >= (cfg['p'] * cfg['v']):
            # Calcul du profit du cycle (Marge 0.02$)
            gain_net = (0.02) * cfg['v']
            st.session_state.profit_total += gain_net
            st.session_state.bot_profits[p_idx] += gain_net
            st.session_state.cycles[p_idx] += 1
            
            # Relance automatique
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': cfg['p'] + 0.02}}
            kraken.create_limit_buy_order('XRP/USDC', cfg['v'], cfg['p'], params)
            st.rerun()

        # --- TITRE PRO NETTOYÉ POUR IPHONE ---
        status = "🟢" if mission_active else "⚪"
        p_net = st.session_state.bot_profits[p_idx]
        titre = f"{status} | 🧾 {montant_reel:.2f}$ | BOT {p_idx} | 🔄 {st.session_state.cycles[p_idx]} | 💰 +{p_net:.4f}$"

        with st.expander(titre, expanded=(p_idx==1)):
            p_in = st.number_input(f"ACHAT B{p_idx}", value=cfg['p'], format="%.4f", key=f"in{p_idx}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{p_idx}")

            c1, c2 = st.columns(2)
            if c1.button(f"🚀 LANCER B{p_idx}", key=f"run{p_idx}"):
                st.session_state.bot_active[p_idx] = True
                if usdc_dispo >= (p_in * cfg['v']):
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', cfg['v'], p_in, params)
                    st.rerun()

            if c2.button(f"🗑️ STOP B{p_idx}", key=f"stop{p_idx}"):
                st.session_state.bot_active[p_idx] = False
                for o in orders:
                    if abs(float(o['amount']) - cfg['v']) < 0.01:
                        kraken.cancel_order(o['id'])
                st.rerun()

    # LISTE RÉELLE KRAKEN
    st.divider()
    st.write("### 📦 MISSIONS ACTIVES")
    if orders:
        for o in orders:
            ico = "🎯 ACHAT" if o['side'] == 'buy' else "💰 VENTE"
            st.info(f"{ico} {o['amount']} XRP @ {o['price']} $")

    if st.button("🚨 RESET TOTAL (PROFITS & CYCLES)"):
        st.session_state.profit_total = 0.0
        st.session_state.bot_profits = {1:0.0, 2:0.0, 3:0.0, 4:0.0}
        st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
