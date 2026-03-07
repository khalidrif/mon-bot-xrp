import streamlit as st
import ccxt
import time

# Configuration iPhone
st.set_page_config(page_title="XRP Sniper Manuel", layout="centered")

try:
    # 1. CONNEXION KRAKEN (FIX NONCE)
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    # Lecture en direct de Kraken (Pas de mémoire cache)
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    # HEADER SIMPLE
    st.write(f"### 🔵 SOLDE LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    # 2. LES 4 TIROIRS (BOTS)
    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # Le voyant est VERT seulement si l'ordre est RÉELLEMENT chez Kraken
        is_on_kraken = any(abs(float(o['price']) - p_base) < 0.05 for o in orders)
        status = "🟢 EN MISSION" if is_on_kraken else "⚪ À L'ARRÊT"
        
        with st.expander(f"🚜 BOT {p_idx} | {status}"):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            col_l, col_s = st.columns(2)
            
            # LANCER : Crée l'achat + la vente liée (Une seule fois)
            if col_l.button(f"🚀 LANCER", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success("Ordre envoyé !")
                    time.sleep(2)
                    st.rerun()

            # STOP : Annule l'ordre et ne fait PLUS RIEN
            if col_s.button(f"🗑️ STOP", key=f"stop{i}"):
                for o in orders:
                    p_o = float(o['price'])
                    if abs(p_o - p_in) < 0.05 or abs(p_o - p_out) < 0.05:
                        kraken.cancel_order(o['id'])
                st.warning("Mission annulée.")
                time.sleep(1)
                st.rerun()

    # 3. LISTE DES MISSIONS RÉELLES
    st.divider()
    st.write("### 📦 MISSIONS SUR KRAKEN")
    if orders:
        for o in orders:
            side = "🎯 ACHAT" if o['side'] == 'buy' else "💰 VENTE"
            st.info(f"{side} {o['amount']} XRP @ {o['price']} $")
    else:
        st.write("Aucune mission active.")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
