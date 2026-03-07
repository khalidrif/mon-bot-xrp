import streamlit as st
import ccxt
import time

st.set_page_config(page_title="XRP Sniper 100% MANUEL", layout="centered")

try:
    # 1. CONNEXION KRAKEN
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    st.write(f"### 🔵 LIBRE SUR KRAKEN : {usdc_dispo:.2f} $")
    st.divider()

    # PRIX DES 4 BOTS
    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # DÉTECTION : VERT seulement si l'ordre est physiquement chez Kraken
        mission_active = False
        for o in orders:
            if abs(float(o['price']) - p_base) < 0.05 or abs(float(o['price']) - (p_base + 0.02)) < 0.05:
                mission_active = True
                break

        status = "🟢 EN MISSION" if mission_active else "⚪ À L'ARRÊT"
        
        with st.expander(f"🚜 BOT {p_idx} | {status}"):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = round(p_in + 0.02, 4)

            # --- ICI : PLUS AUCUN CODE DE RACHAT AUTOMATIQUE ---

            col_l, col_s = st.columns(2)
            
            if col_l.button(f"🚀 LANCER L'ORDRE", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success("Ordre envoyé à Kraken !")
                    time.sleep(2)
                    st.rerun()

            if col_s.button(f"🗑️ STOP / ANNULER", key=f"stop{i}"):
                for o in orders:
                    # Annule tout ce qui est proche du prix du bot
                    if abs(float(o['price']) - p_in) < 0.05 or abs(float(o['price']) - p_out) < 0.05:
                        kraken.cancel_order(o['id'])
                st.warning("Ordre annulé. Le bot ne bougera plus.")
                time.sleep(2)
                st.rerun()

    # LISTE RÉELLE DES MISSIONS
    st.divider()
    st.write("### 📦 TES ORDRES SUR KRAKEN")
    if orders:
        for o in orders:
            st.info(f"{o['side'].upper()} {o['amount']} XRP @ {o['price']} $")
    else:
        st.write("Aucun ordre en cours.")

except Exception as e:
    st.error(f"Erreur Kraken : {e}")

time.sleep(60)
st.rerun()
