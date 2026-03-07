import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DE SÉCURITÉ (VERROUS)
if 'active_bots' not in st.session_state: st.session_state.active_bots = {} 
if 'lock' not in st.session_state: st.session_state.lock = False # Verrou anti-double clic
if 'profit_reel' not in st.session_state: st.session_state.profit_reel = 0.0

st.set_page_config(page_title="XRP Sniper Zero-Double", layout="centered")
st.markdown("<style>.stApp { background: #F8F9FA; } .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }</style>", unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    st.write(f"### 🔵 LIBRE : {usdc_dispo:.2f} $ | 📈 PRIX : {prix_actuel:.4f} $")

    orders = kraken.fetch_open_orders('XRP/USDC')
    prices_in = [1.3600, 1.3400, 1.3200]

    for i in range(3):
        p_idx = i + 1
        p_cible = prices_in[i]
        # Vérification physique sur Kraken
        deja_en_cours = any(float(o['price']) == p_cible for o in orders)
        
        with st.expander(f"🚜 BOT {p_idx} | {'🟢 ACTIF' if deja_en_cours else '⚪ INACTIF'}"):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            m_invest = st.number_input("MONTANT $", value=15.0, min_value=14.0, key=f"m{i}")
            p_in = st.number_input("ACHAT", value=p_cible, format="%.4f", key=f"in{i}")
            p_out = st.number_input("VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # --- BOULE DE NEIGE ---
            if p_idx in st.session_state.active_bots and not deja_en_cours and not st.session_state.lock:
                if usdc_dispo >= m_invest:
                    st.session_state.lock = True # ON VERROUILLE
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    time.sleep(2) # PAUSE SÉCURITÉ
                    st.session_state.lock = False # ON LIBÈRE
                    st.rerun()

            col_l, col_s = st.columns(2)
            
            # --- LANCER (AVEC ANTI-DOUBLON) ---
            if col_l.button(f"🚀 LANCER", key=f"run{i}"):
                if not deja_en_cours and usdc_dispo >= m_invest and not st.session_state.lock:
                    st.session_state.lock = True # ON VERROUILLE
                    st.session_state.active_bots[p_idx] = True
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    time.sleep(2) # PAUSE SÉCURITÉ
                    st.session_state.lock = False # ON LIBÈRE
                    st.success("Ordre unique envoyé !")
                    st.rerun()

            if col_s.button(f"🗑️ STOP", key=f"stop{i}"):
                if p_idx in st.session_state.active_bots: del st.session_state.active_bots[p_idx]
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # MISSIONS
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES")
    if orders:
        for o in orders:
            st.info(f"🎯 {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
