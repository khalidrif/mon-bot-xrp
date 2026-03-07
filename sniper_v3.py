import streamlit as st
import ccxt
import time

# 1. CONFIGURATION INTERFACE
st.set_page_config(page_title="XRP Sniper Master V3", layout="centered")

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

    st.write(f"### 🔵 SOLDE LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    # PRIX FIXES POUR CHAQUE BOT
    # B1: 1.365 | B2: 1.34 | B3: 1.32 | B4: 1.30
    prices_fixed = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_fixed[i]
        
        # --- DÉTECTION CHIRURGICALE : UN BOT = UN PRIX ---
        mission_active = False
        montant_engage = 0.0
        for o in orders:
            p_o = float(o['price'])
            # Le bot 1 ne voit QUE 1.365, le bot 2 ne voit QUE 1.34
            if abs(p_o - p_base) < 0.001 or abs(p_o - (p_base + 0.02)) < 0.001:
                mission_active = True
                montant_engage = float(o['amount']) * p_o
                break

        # TITRE UNIQUE POUR CHAQUE BARRE
        if mission_active:
            titre = f"🟢 EN MISSION | {montant_engage:.2f} $ | BOT {p_idx}"
        else:
            titre = f"⚪ À L'ARRÊT | BOT {p_idx}"

        with st.expander(titre, expanded=(i==0)):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            c1, c2 = st.columns(2)
            if c1.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

            if c2.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                for o in orders:
                    p_o = float(o['price'])
                    if abs(p_o - p_in) < 0.005 or abs(p_o - p_out) < 0.005:
                        kraken.cancel_order(o['id'])
                st.rerun()

    # LISTE DES MISSIONS RÉELLES
    st.divider()
    st.write("### 📦 MISSIONS ACTIVES")
    for o in orders:
        st.info(f"{o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
