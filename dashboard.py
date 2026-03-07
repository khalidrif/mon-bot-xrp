import streamlit as st
import ccxt
import time

# 1. STYLE PRO
st.set_page_config(page_title="XRP Sniper Live", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 20px; padding: 15px; text-align: center; color: white; margin-bottom: 10px; }
    .summary-card { background: white; padding: 15px; border-radius: 20px; border: 2px solid #28a745; text-align: center; margin-bottom: 20px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_total = balance['total'].get('USDC', 0.0)
    usdc_dispo = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # HEADER
    st.markdown(f'<div class="cumul-box"><p style="margin:0; opacity:0.8;">SOLDE KRAKEN</p><h1>{usdc_total:.2f} $</h1></div>', unsafe_allow_html=True)
    
    # --- BLOC UNIQUE : RÉSUMÉ DES PROFITS ---
    # On calcule le profit total potentiel de la grille de 3 bots
    vol_calc = (usdc_total * 0.95 / 3) / prix_actuel
    profit_total_estime = (vol_calc * 0.02 * 3) - (usdc_total * 0.0052) # Gain - Frais (0.26% x 2)
    
    st.markdown(f"""
        <div class="summary-card">
            <h3 style="margin:0; color:#28a745;">📈 RÉSUMÉ DE LA STRATÉGIE</h3>
            <p style="margin:0; font-size:1.2rem;"><b>Profit Net Total : +{max(0, profit_total_estime):.2f} $</b></p>
            <p style="margin:0; font-size:0.8rem; color:grey;">(Si les 3 bots terminent leur cycle)</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.metric("DISPO", f"{usdc_dispo:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # --- LISTE DES BOTS ---
    prices_in = [1.3600, 1.3400, 1.3200]
    for i in range(3):
        p_idx = i + 1
        with st.expander(f"🚜 RÉGLAGES BOT {p_idx}", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            p_in = st.number_input(f"ACHAT", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE", value=p_in + 0.02, format="%.4f", key=f"out{i}")
            
            col_l, col_s = st.columns(2)
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo > 13.5:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_calc, p_in, params)
                    st.success("OK")
                    st.balloons()
            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                orders = kraken.fetch_open_orders('XRP/USDC')
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # MISSIONS
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES")
    orders = kraken.fetch_open_orders('XRP/USDC')
    for o in orders:
        st.info(f"🎯 {o['side'].upper()} {o['amount']:.1f} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
