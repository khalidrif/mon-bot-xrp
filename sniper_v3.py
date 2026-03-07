import streamlit as st
import ccxt
import time

# 1. CONFIGURATION INTERFACE IPHONE
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

    # --- CONFIGURATION UNIQUE PAR BOT (EMPREINTE DIGITALE) ---
    # On donne un volume légèrement différent à chaque bot pour les distinguer
    bot_configs = {
        1: {"p": 1.3650, "v": 10.6},
        2: {"p": 1.3400, "v": 10.8},
        3: {"p": 1.3200, "v": 11.0},
        4: {"p": 1.3000, "v": 11.2}
    }

    for p_idx, cfg in bot_configs.items():
        # DÉTECTION PAR VOLUME UNIQUE (ANTI-CONFUSION)
        mission_active = False
        montant_reel = 0.0
        
        for o in orders:
            # Le bot ne s'allume QUE s'il voit SON volume précis (ex: 10.8 pour B2)
            if abs(float(o['amount']) - cfg['v']) < 0.01:
                mission_active = True
                montant_reel = float(o['amount']) * float(o['price'])
                break

        # TITRE AVEC VOYANT
        status = "🟢 EN MISSION" if mission_active else "⚪ À L'ARRÊT"
        titre = f"{status} | {montant_reel:.2f} $ | BOT {p_idx}"

        with st.expander(titre, expanded=(p_idx==1)):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=round(cfg['v'] * cfg['p'], 2), key=f"m{p_idx}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=cfg['p'], format="%.4f", key=f"in{p_idx}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{p_idx}")

            c1, c2 = st.columns(2)
            if c1.button(f"🚀 LANCER B{p_idx}", key=f"run{p_idx}"):
                if usdc_dispo >= m_invest:
                    # On utilise le volume unique du bot
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', cfg['v'], p_in, params)
                    st.rerun()

            if c2.button(f"🗑️ STOP B{p_idx}", key=f"stop{p_idx}"):
                for o in orders:
                    if abs(float(o['amount']) - cfg['v']) < 0.01:
                        kraken.cancel_order(o['id'])
                st.rerun()

    # LISTE RÉELLE KRAKEN
    st.divider()
    st.write("### 📦 MISSIONS ACTIVES")
    for o in orders:
        st.info(f"{o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
