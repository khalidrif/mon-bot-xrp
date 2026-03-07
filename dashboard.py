import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES ÉTATS (VERROUS)
if 'bot_active' not in st.session_state:
    st.session_state.bot_active = {1: False, 2: False, 3: False}
if 'profit_reel' not in st.session_state:
    st.session_state.profit_reel = 0.0

st.set_page_config(page_title="XRP Sniper Libre", layout="centered")

try:
    # 2. CONNEXION ET PRIX
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)

    # HEADER
    st.write(f"### 💰 PROFIT : {st.session_state.profit_reel:.2f} $ | 🔵 LIBRE : {usdc_dispo:.2f} $")

    # 3. LES BOTS (DÉTECTION PAR MÉMOIRE, PAS PAR PRIX)
    prices_in = [1.3650, 1.3400, 1.3200]
    orders = kraken.fetch_open_orders('XRP/USDC')

    for i in range(3):
        p_idx = i + 1
        # ICI : Le bot est vert si TU l'as activé, peu importe le prix !
        is_running = st.session_state.bot_active[p_idx]
        status_color = "🟢 ACTIF" if is_running else "⚪ INACTIF"
        
        with st.expander(f"🚜 BOT {p_idx} | {status_color}", expanded=(i==0)):
            m_invest = st.number_input("MONTANT $", value=16.0, min_value=14.0, key=f"m{i}")
            p_in = st.number_input("ACHAT", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input("VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # --- BOULE DE NEIGE ---
            # Si le bot est activé mais que l'ordre n'est plus sur Kraken (vente finie)
            deja_sur_kraken = any(float(o['price']) == p_in for o in orders)
            if is_running and not deja_sur_kraken and usdc_dispo >= m_invest:
                vol = round(m_invest / p_in, 1)
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            col_l, col_s = st.columns(2)
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    st.session_state.bot_active[p_idx] = True # ON ALLUME LE VOYANT
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                st.session_state.bot_active[p_idx] = False # ON ÉTEINT LE VOYANT
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()

    # MISSIONS RÉELLES
    st.divider()
    st.markdown("### 📦 MISSIONS SUR KRAKEN")
    for o in orders:
        st.info(f"🎯 {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
