import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES PROFITS
if 'profit_reel' not in st.session_state: st.session_state.profit_reel = 0.0

st.set_page_config(page_title="XRP Compound Bot", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); }
    .profit-box { background: #28a745; color: white; padding: 15px; border-radius: 20px; text-align: center; margin-bottom: 10px; }
    .status-box { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 15px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION KRAKEN
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_total = balance['total'].get('USDC', 0.0)
    usdc_dispo = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # HEADER
    st.markdown(f'<div class="profit-box">PROFIT TOTAL : + {st.session_state.profit_reel:.2f} $</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box"><p style="margin:0; color:grey;">CAPITAL TOTAL</p><h2>{usdc_total:.2f} $</h2></div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    col_a.metric("LIBRE (DÉPÔTS)", f"{usdc_dispo:.2f} $")
    col_b.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. LOGIQUE BOULE DE NEIGE PAR BOT
    orders = kraken.fetch_open_orders('XRP/USDC')
    prices_in = [1.3600, 1.3400, 1.3200]

    for i in range(3):
        p_idx = i + 1
        p_cible = prices_in[i]
        
        # On vérifie si ce bot a une mission en cours
        a_un_ordre = any(float(o['price']) == p_cible for o in orders)
        
        status = " | 🟢 EN MISSION" if a_un_ordre else " | 😴 EN ATTENTE"
        
        with st.expander(f"🚜 BOT {p_idx}{status}", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            
            m_invest = st.number_input("MONTANT $", value=15.0, min_value=0.0, step=1.0, key=f"m{i}")
            p_in = st.number_input("PRIX ACHAT", value=p_cible, format="%.4f", key=f"in{i}")
            p_out = st.number_input("PRIX VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # --- AUTO-RELANCE (BOULE DE NEIGE) ---
            # Si le bot est "En attente" mais qu'on a du cash (retour de vente), il se relance
            if not a_un_ordre and usdc_dispo >= m_invest and m_invest >= 14.0:
                st.warning(f"🔄 Relance automatique de B{p_idx}...")
                vol = round(m_invest / p_in, 1)
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            col_l, col_s = st.columns(2)
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success("C'est parti !")
                    st.rerun()
                else: st.error("Pas assez de USDC libres")

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # MISSIONS
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES")
    if orders:
        for o in orders:
            ico = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

    if st.button("🚨 RESET TOTAL", use_container_width=True):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
