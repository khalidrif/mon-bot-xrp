import streamlit as st
import ccxt
import time

# 1. MÉMOIRE NETTOYÉE
if 'bot_active' not in st.session_state:
    st.session_state.bot_active = {1: False, 2: False, 3: False, 4: False}

st.set_page_config(page_title="XRP Sniper 100% Manuel", layout="centered")

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

    st.write(f"### 🔵 LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # DÉTECTION STRICTE : Le voyant est VERT seulement s'il y a un ORDRE RÉEL
        mission_active = any(abs(float(o['price']) - p_base) < 0.01 for o in orders)
        status = "🟢 ACTIF" if mission_active else "⚪ INACTIF"
        
        with st.expander(f"🚜 BOT {p_idx} | {status}"):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = round(p_in + 0.02, 4)

            # --- AUCUNE BOULE DE NEIGE ICI ---
            # Le bot ne relance JAMAIS d'achat tout seul.

            col_l, col_s = st.columns(2)
            
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                for o in orders:
                    # On annule tout ce qui touche au prix de ce bot
                    if abs(float(o['price']) - p_in) < 0.05 or abs(float(o['price']) - p_out) < 0.05:
                        kraken.cancel_order(o['id'])
                st.rerun()

    st.divider()
    st.write("### 📦 MISSIONS SUR KRAKEN")
    for o in orders:
        st.info(f"{o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(30)
st.rerun()
