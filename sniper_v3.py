import streamlit as st
import ccxt
import time

# 1. CONFIGURATION INTERFACE PRO
st.set_page_config(page_title="XRP Sniper Master V3", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .main-box { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION KRAKEN
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    # HEADER : TON TRÉSOR
    st.markdown(f"""
        <div class="main-box">
            <p style="color: grey; margin-bottom: 5px;">SOLDE LIBRE</p>
            <h1 style="color: #1E1E1E; margin-top: 0;">{usdc_dispo:.2f} $</h1>
            <p style="color: #007BFF; font-weight: bold;">📈 PRIX XRP : {prix_actuel:.4f} $</p>
        </div>
    """, unsafe_allow_html=True)

    # 3. LES 4 SNIPERS INDÉPENDANTS
    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # RÉGLAGES DU BOT (DÉPLACÉS POUR UNE DÉTECTION PRÉCISE)
        with st.expander(f"BOT {p_idx}", expanded=(i==0)):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # --- DÉTECTION ULTRA-STRICTE (ANTI-FANTÔME) ---
            mission_active = False
            montant_engage = 0.0
            for o in orders:
                p_o = float(o['price'])
                # On ne s'allume QUE si le prix de l'ordre est IDENTIQUE au réglage (marge de 0.0001)
                if abs(p_o - p_in) < 0.0001 or abs(p_o - p_out) < 0.0001:
                    mission_active = True
                    montant_engage = float(o['amount']) * p_o
                    break

            # CONSTRUCTION DU TITRE DYNAMIQUE
            status_txt = "🟢 EN MISSION" if mission_active else "⚪ À L'ARRÊT"
            montant_txt = f" | {montant_engage:.2f} $" if mission_active else ""
            st.markdown(f"### {status_txt}{montant_txt}")

            c1, c2 = st.columns(2)
            if c1.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

            if c2.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                for o in orders:
                    p_o = float(o['price'])
                    if abs(p_o - p_in) < 0.001 or abs(p_o - p_out) < 0.001:
                        kraken.cancel_order(o['id'])
                st.rerun()

    # MISSIONS RÉELLES
    st.divider()
    st.write("### 📦 MISSIONS ACTIVES SUR KRAKEN")
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
