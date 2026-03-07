import streamlit as st
import ccxt
import time

# 1. CONFIGURATION INTERFACE PRO
st.set_page_config(page_title="XRP Sniper Master V3", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .main-box { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; height: 50px; transition: 0.3s; }
    .btn-market { background-color: #FF4B4B !important; color: white !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION KRAKEN (TES NOUVEAUX SECRETS)
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    # Lecture des données réelles
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    xrp_dispo = balance['free'].get('XRP', 0.0)
    
    # Calcul du Capital Total (USDC + Valeur des XRP)
    valeur_xrp = xrp_dispo * prix_actuel
    capital_total = usdc_dispo + valeur_xrp + sum(float(o['amount']) * float(o['price']) for o in kraken.fetch_open_orders('XRP/USDC'))
    
    orders = kraken.fetch_open_orders('XRP/USDC')

    # --- HEADER : TON TRÉSOR ---
    st.markdown(f"""
        <div class="main-box">
            <p style="color: grey; margin-bottom: 5px;">CAPITAL TOTAL (ESTIMÉ)</p>
            <h1 style="color: #1E1E1E; margin-top: 0;">{capital_total:.2f} $</h1>
            <p style="color: #007BFF; font-weight: bold;">🔵 LIBRE : {usdc_dispo:.2f} $ | 📈 XRP : {prix_actuel:.4f} $</p>
        </div>
    """, unsafe_allow_html=True)

    # 3. LES 4 SNIPERS INDÉPENDANTS
    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        with st.expander(f"🚜 BOT {p_idx}", expanded=(i==0)):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # DÉTECTION PRÉCISE : Seul le bot au bon prix s'allume
            mission_active = any(abs(float(o['price']) - p_in) < 0.0005 or abs(float(o['price']) - p_out) < 0.0005 for o in orders)
            status_txt = "🟢 EN MISSION" if mission_active else "⚪ À L'ARRÊT"
            st.write(f"**STATUT : {status_txt}**")

            c1, c2 = st.columns(2)
            if c1.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

            if c2.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                for o in orders:
                    if abs(float(o['price']) - p_in) < 0.001 or abs(float(o['price']) - p_out) < 0.001:
                        kraken.cancel_order(o['id'])
                st.rerun()

    # --- BOUTON DE SÉCURITÉ MARCHÉ ---
    st.divider()
    if st.button("🚨 VENDRE TOUT AU PRIX DU MARCHÉ", help="Annule tout et vend tes XRP immédiatement", use_container_width=True):
        kraken.cancel_all_orders('XRP/USDC')
        if xrp_dispo > 10: # Minimum Kraken
            kraken.create_market_sell_order('XRP/USDC', xrp_dispo)
            st.warning("Tout a été vendu au marché !")
        st.rerun()

    # MISSIONS RÉELLES
    st.write("### 📦 TES MISSIONS ACTIVES")
    for o in orders:
        side = "🎯 ACHAT" if o['side'] == 'buy' else "💰 VENTE"
        st.info(f"{side} {o['amount']} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
