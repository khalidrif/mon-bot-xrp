import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES ÉTATS, PROFITS ET CYCLES
if 'active_bots' not in st.session_state: 
    st.session_state.active_bots = {1:False, 2:False, 3:False, 4:False} 
if 'profit_reel' not in st.session_state: st.session_state.profit_reel = 0.0
if 'cycles' not in st.session_state: 
    st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
if 'last_click' not in st.session_state: st.session_state.last_click = 0

st.set_page_config(page_title="XRP Sniper Master", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .profit-box { background: #28a745; color: white; padding: 15px; border-radius: 20px; text-align: center; margin-bottom: 10px; }
    .status-box { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 15px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; height: 48px; background-color: #F3BA2F !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION KRAKEN
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])
    balance = kraken.fetch_balance()
    usdc_total = balance['total'].get('USDC', 0.0)
    usdc_dispo = balance['free'].get('USDC', 0.0)

    # HEADER : PROFIT TOTAL ET CAPITAL
    st.markdown(f'<div class="profit-box">💰 PROFIT TOTAL : + {st.session_state.profit_reel:.2f} $</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box"><p style="margin:0; color:grey;">CAPITAL TOTAL</p><h2>{usdc_total:.2f} $</h2></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("LIBRE (USDC)", f"{usdc_dispo:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. INTERFACE DES 4 BOTS
    orders = kraken.fetch_open_orders('XRP/USDC')
    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # DÉTECTION INTELLIGENTE
        mission_active = False
        montant_reel = 0.0
        for o in orders:
            p_o = float(o['price'])
            if (i == 0 and p_o > 1.35) or (i == 1 and 1.33 <= p_o <= 1.35) or \
               (i == 2 and 1.31 <= p_o < 1.33) or (i == 3 and p_o < 1.31):
                mission_active = True
                montant_reel = float(o['amount']) * p_o
                break

        status_txt = "🟢 ACTIF" if mission_active else "⚪ INACTIF"
        nb_cycles = st.session_state.cycles[p_idx]
        label_head = f"🚜 BOT {p_idx} | {status_txt} | 🔄 {nb_cycles} Cycles"

        with st.expander(label_head, expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # --- LOGIQUE BOULE DE NEIGE + CALCUL PROFIT + COMPTEUR ---
            if st.session_state.active_bots[p_idx] and not mission_active and usdc_dispo >= m_invest:
                # 1. Calculer le profit du cycle qui vient de finir
                gain_cycle = (p_out - p_in) * (m_invest / p_in)
                st.session_state.profit_reel += gain_cycle
                # 2. Augmenter le compteur de cycles
                st.session_state.cycles[p_idx] += 1
                
                # 3. Relancer l'achat
                vol = round(m_invest / p_in, 1)
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            col_l, col_s = st.columns(2)
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if time.time() - st.session_state.last_click > 5 and usdc_dispo >= m_invest:
                    st.session_state.last_click = time.time()
                    st.session_state.active_bots[p_idx] = True
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success("Mission lancée !")
                    time.sleep(2)
                    st.rerun()

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                st.session_state.active_bots[p_idx] = False
                for o in orders:
                    p_o = float(o['price'])
                    if (i == 0 and p_o > 1.35) or (i == 1 and 1.33 <= p_o <= 1.35) or \
                       (i == 2 and 1.31 <= p_o < 1.33) or (i == 3 and p_o < 1.31):
                        kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # 4. MISSIONS RÉELLES
    st.divider()
    st.markdown("### 📦 MISSIONS SUR KRAKEN")
    if orders:
        for o in orders:
            ico = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

    if st.button("🚨 RESET TOUS LES COMPTEURS"):
        st.session_state.profit_reel = 0.0
        st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
