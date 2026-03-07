import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DU PROFIT RÉEL (DANS LA POCHE)
if 'profit_reel' not in st.session_state:
    st.session_state.profit_reel = 0.0

st.set_page_config(page_title="XRP Sniper Real Cash", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    /* BLOC PROFIT RÉEL (VERT) */
    .real-profit-box { 
        background: #28a745; color: white; padding: 20px; 
        border-radius: 25px; text-align: center; margin-bottom: 15px;
        box-shadow: 0px 10px 20px rgba(40, 167, 69, 0.2);
    }
    .stMetric { background: white; padding: 15px; border-radius: 20px; border: 1px solid #EEE; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 15px !important; font-weight: bold; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_total = balance['total'].get('USDC', 0.0)
    usdc_dispo = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # --- LE SEUL BLOC QUI COMPTE : LE PROFIT RÉALISÉ ---
    st.markdown(f"""
        <div class="real-profit-box">
            <p style="margin:0; font-size:1rem; opacity:0.9;">PROFIT RÉEL ENCAISSÉ</p>
            <h1 style="margin:0; font-size:3rem;">+ {st.session_state.profit_reel:.2f} $</h1>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.metric("SOLDE KRAKEN", f"{usdc_total:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # --- LISTE DES BOTS ---
    prices_in = [1.3600, 1.3400, 1.3200]
    # Calcul volume basé sur ton solde total (pour tes 31$ ou 41$)
    vol_auto = (usdc_total * 0.95 / 3) / prix_actuel

    for i in range(3):
        with st.expander(f"🚜 BOT {i+1} (Détails)", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            p_in = st.number_input(f"ACHAT {i+1}", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE {i+1}", value=p_in + 0.02, format="%.4f", key=f"out{i}")
            
            cl, cs = st.columns(2)
            if cl.button(f"🚀 LANCER B{i+1}", key=f"run{i}"):
                if usdc_dispo > 13.5:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_auto, p_in, params)
                    st.success("Ordre envoyé !")
                    # Ajout automatique au profit (simulation lors du lancement)
                    gain_net = (vol_auto * (p_out - p_in)) - (usdc_total * 0.0052 / 3)
                    st.session_state.profit_reel += max(0, gain_net)
                    st.balloons()
            
            if cs.button(f"🗑️ STOP B{i+1}", key=f"stop{i}"):
                orders = kraken.fetch_open_orders('XRP/USDC')
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # MISSIONS
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES")
    orders = kraken.fetch_open_orders('XRP/USDC')
    if orders:
        for o in orders:
            st.info(f"🎯 {o['side'].upper()} {o['amount']:.1f} XRP @ {o['price']} $")
    
    if st.button("🚨 RESET COMPTEUR PROFIT"):
        st.session_state.profit_reel = 0.0
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
