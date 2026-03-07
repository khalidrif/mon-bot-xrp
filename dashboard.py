import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES ÉTATS (VERROUS) ET DU PROFIT
if 'bot_active' not in st.session_state:
    st.session_state.bot_active = {1: False, 2: False, 3: False}
if 'profit_reel' not in st.session_state:
    st.session_state.profit_reel = 0.0

st.set_page_config(page_title="XRP Sniper Final", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .profit-box { background: #28a745; color: white; padding: 15px; border-radius: 20px; text-align: center; margin-bottom: 10px; box-shadow: 0px 4px 15px rgba(40,167,69,0.2); }
    .status-box { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 15px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; height: 45px; }
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

    # AFFICHAGE CAPITAL ET PROFIT
    st.markdown(f'<div class="profit-box">PROFIT RÉEL : + {st.session_state.profit_reel:.2f} $</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box"><p style="margin:0; color:grey;">CAPITAL TOTAL KRAKEN</p><h2>{usdc_total:.2f} $</h2></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("LIBRE (DÉPÔTS)", f"{usdc_dispo:.2f} $")
    c2.metric("PRIX XRP LIVE", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. INTERFACE DES 3 BOTS
    orders = kraken.fetch_open_orders('XRP/USDC')
    prices_in = [1.3600, 1.3400, 1.3200]

    for i in range(3):
        p_idx = i + 1
        p_cible = prices_in[i]
        
        # Vérification si un ordre est déjà sur Kraken
        a_un_ordre = any(float(o['price']) == p_cible for o in orders)
        status_label = "🟢 ACTIF" if a_un_ordre else "🔴 ARRÊTÉ"
        
        # Titre dynamique avec montant engagé
        montant_engage = 0.0
        for o in orders:
            if float(o['price']) == p_cible:
                montant_engage = float(o['amount']) * float(o['price'])
        
        with st.expander(f"🚜 BOT {p_idx} | {status_label} ({montant_engage:.2f}$)", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            
            m_invest = st.number_input("MONTANT ($)", value=15.0, min_value=0.0, step=1.0, key=f"m{i}")
            p_in = st.number_input("ACHAT", value=p_cible, format="%.4f", key=f"in{i}")
            p_out = st.number_input("VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # --- BOULE DE NEIGE SÉCURISÉE ---
            if st.session_state.bot_active[p_idx] and not a_un_ordre and usdc_dispo >= m_invest:
                vol = round(m_invest / p_in, 1)
                if vol >= 10:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

            col_l, col_s = st.columns(2)
            
            # BOUTON LANCER
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo >= m_invest and m_invest >= 14.0:
                    st.session_state.bot_active[p_idx] = True # VERROU ON
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success("Mission démarrée !")
                    time.sleep(1)
                    st.rerun()
                else: st.error("Solde insuffisant ou < 14$")

            # BOUTON STOP
            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                st.session_state.bot_active[p_idx] = False # VERROU OFF
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # 4. MISSIONS ACTIVES
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES SUR KRAKEN")
    if orders:
        for o in orders:
            ico = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")
    else:
        st.write("Aucune mission active.")

    if st.button("🚨 RESET COMPTEUR PROFIT"):
        st.session_state.profit_reel = 0.0
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
