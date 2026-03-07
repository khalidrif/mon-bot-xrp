import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES PROFITS ET ÉTATS
if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0
if 'last_click' not in st.session_state: st.session_state.last_click = 0

st.set_page_config(page_title="XRP Sniper Manual", layout="centered")
st.markdown("""
    <style>
    .stApp { background: #F8F9FA; }
    .profit-box { background: #28a745; color: white; padding: 15px; border-radius: 20px; text-align: center; margin-bottom: 10px; }
    .status-box { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 15px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; height: 45px; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION KRAKEN
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    usdc_total = balance['total'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # HEADER
    st.markdown(f'<div class="profit-box">PROFIT RÉEL : + {st.session_state.profit_total:.2f} $</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box"><p style="margin:0; color:grey;">CAPITAL TOTAL</p><h2>{usdc_total:.2f} $</h2></div>', unsafe_allow_html=True)
    st.write(f"### 🔵 LIBRE : {usdc_dispo:.2f} $ | 📈 PRIX : {prix_actuel:.4f} $")

    st.divider()

    # 3. INTERFACE 3 BOTS MANUELS
    orders = kraken.fetch_open_orders('XRP/USDC')
    prices_in = [1.3600, 1.3400, 1.3200]

    for i in range(3):
        p_idx = i + 1
        p_cible = prices_in[i]
        
        # Vérification si un ordre est déjà sur Kraken
        deja_en_cours = any(float(o['price']) == p_cible for o in orders)
        status_label = "🟢 ACTIF" if deja_en_cours else "⚪ INACTIF"
        
        with st.expander(f"🚜 BOT {p_idx} | {status_label}", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            
            # RÉGLAGES (Sécurité à 14$ pour Kraken)
            m_invest = st.number_input("MONTANT ($)", value=16.0, min_value=14.0, step=0.5, key=f"m{i}")
            p_in = st.number_input("ACHAT", value=p_cible, format="%.4f", key=f"in{i}")
            p_out = st.number_input("VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            col_l, col_s = st.columns(2)
            
            # LANCER : 1 Clic = 1 Ordre Manuel
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                maintenant = time.time()
                if maintenant - st.session_state.last_click < 5:
                    st.warning("Attends 5 secondes...")
                elif deja_en_cours:
                    st.error("Déjà un ordre à ce prix !")
                elif usdc_dispo < m_invest:
                    st.error("Solde insuffisant")
                else:
                    st.session_state.last_click = maintenant
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success("Ordre envoyé !")
                    time.sleep(2)
                    st.rerun()

            # STOP : Annule seulement cet ordre
            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # 4. MISSIONS ACTIVES
    st.divider()
    st.markdown("### 📦 MISSIONS SUR KRAKEN")
    if orders:
        for o in orders:
            ico = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

    if st.button("🚨 RESET TOTAL (STOP TOUT)"):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
