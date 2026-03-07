import streamlit as st
import ccxt
import time

# 1. MÉMOIRE ET SÉCURITÉ
if 'profit_reel' not in st.session_state: st.session_state.profit_reel = 0.0
if 'last_click' not in st.session_state: st.session_state.last_click = 0
if 'active_bots' not in st.session_state: st.session_state.active_bots = {}

st.set_page_config(page_title="XRP Sniper Pro", layout="centered")
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

    # HEADER
    st.markdown(f'<div class="profit-box">PROFIT RÉEL : + {st.session_state.profit_reel:.2f} $</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box"><p style="margin:0; color:grey;">CAPITAL TOTAL</p><h2>{usdc_total:.2f} $</h2></div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    col_a.metric("LIBRE (SCAN)", f"{usdc_dispo:.2f} $")
    col_b.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. DÉTECTION INTELLIGENTE PAR ZONE
    orders = kraken.fetch_open_orders('XRP/USDC')
    prices_in = [1.3650, 1.3400, 1.3200]

    for i in range(3):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # Détection automatique de la mission dans la zone
        mission_active = False
        montant_bot = 0.0
        for o in orders:
            p_o = float(o['price'])
            # B1: >1.35 | B2: 1.33-1.35 | B3: <1.33
            if (i == 0 and p_o > 1.35) or (i == 1 and 1.33 <= p_o <= 1.35) or (i == 2 and p_o < 1.33):
                mission_active = True
                montant_bot = float(o['amount']) * p_o
                break

        status_txt = "🟢 ACTIF" if mission_active else "⚪ INACTIF"
        label_cash = f" | 📦 {montant_bot:.2f} $" if montant_bot > 0 else ""

        with st.expander(f"🚜 BOT {p_idx} | {status_txt}{label_cash}", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            m_invest = st.number_input("MONTANT $", value=16.0, min_value=14.0, key=f"m{i}")
            p_in = st.number_input("ACHAT", value=p_base, format="%.4f", key=f"in{i}")
            p_out = st.number_input("VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # BOULE DE NEIGE : Relance si activé en mémoire
            if p_idx in st.session_state.active_bots and not mission_active and usdc_dispo >= m_invest:
                vol = round(m_invest / p_in, 1)
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                st.rerun()

            col_l, col_s = st.columns(2)
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                maintenant = time.time()
                if maintenant - st.session_state.last_click < 5:
                    st.warning("Attends 5 secondes...")
                elif mission_active:
                    st.error("Déjà en mission !")
                elif usdc_dispo < m_invest:
                    st.error("Solde insuffisant")
                else:
                    st.session_state.last_click = maintenant
                    st.session_state.active_bots[p_idx] = True
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success("Mission lancée !")
                    time.sleep(2)
                    st.rerun()

            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                if p_idx in st.session_state.active_bots: del st.session_state.active_bots[p_idx]
                for o in orders:
                    p_o = float(o['price'])
                    if (i == 0 and p_o > 1.35) or (i == 1 and 1.33 <= p_o <= 1.35) or (i == 2 and p_o < 1.33):
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

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
