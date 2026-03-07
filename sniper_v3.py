import streamlit as st
import ccxt
import time

# CONFIGURATION IPHONE - SÉCURITÉ MAXIMALE
st.set_page_config(page_title="XRP Sniper Manuel V3", layout="centered")

try:
    # 1. CONNEXION KRAKEN (RÉCUPÈRE TES SECRETS)
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    # LECTURE DIRECTE DU COMPTE (PAS DE MÉMOIRE FANTÔME)
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    # HEADER SIMPLE - TON CAPITAL RÉEL
    st.write(f"### 🔵 SOLDE LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    # 2. LES 4 SNIPERS (MODE OBÉISSANCE TOTALE)
    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # LE VOYANT EST VERT SEULEMENT SI L'ORDRE EST CHEZ KRAKEN
        mission_active = False
        for o in orders:
            p_o = float(o['price'])
            if abs(p_o - p_base) < 0.05 or abs(p_o - (p_base + 0.02)) < 0.05:
                mission_active = True
                break

        status = "🟢 MISSION EN COURS" if mission_active else "⚪ BOT À L'ARRÊT"
        
        with st.expander(f"🚜 BOT {p_idx} | {status}"):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"PRIX ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"PRIX VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            col_l, col_s = st.columns(2)
            
            # LANCER : UN SEUL CLIC = UN SEUL ORDRE (PAS DE RELANCE AUTO)
            if col_l.button(f"🚀 LANCER CYCLE", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success("Ordre envoyé !")
                    time.sleep(2)
                    st.rerun()

            # STOP : ANNULE ET RESTE GRIS (DÉFINITIF)
            if col_s.button(f"🗑️ STOP / ANNULER", key=f"stop{i}"):
                for o in orders:
                    p_o = float(o['price'])
                    if abs(p_o - p_in) < 0.05 or abs(p_o - p_out) < 0.05:
                        kraken.cancel_order(o['id'])
                st.warning("Mission annulée.")
                time.sleep(1)
                st.rerun()

    # 3. LA LISTE DES MISSIONS RÉELLES
    st.divider()
    st.write("### 📦 TES MISSIONS SUR KRAKEN")
    if orders:
        for o in orders:
            ico = "🎯 ACHAT" if o['side'] == 'buy' else "💰 VENTE"
            st.info(f"{ico} {o['amount']} XRP @ {o['price']} $")
    else:
        st.write("Aucune mission active. Ton argent dort en sécurité.")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
