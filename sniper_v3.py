import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE (3 Boîtes Verticales)
st.set_page_config(page_title="XRP Sniper 3-Bots", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .status-box { background: #28a745; color: white; padding: 15px; border-radius: 20px; text-align: center; margin-bottom: 10px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.03); }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; height: 45px; }
    </style>
    """, unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_total = balance['total'].get('USDC', 0.0)
    usdc_dispo = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # HEADER : TON SOLDE AVEC LES 17$ INCLUS
    st.markdown(f'<div class="status-box"><p style="margin:0; opacity:0.8;">CAPITAL TOTAL (SCAN)</p><h1>{usdc_total:.2f} $</h1></div>', unsafe_allow_html=True)
    st.metric("DISPO (POUR LANCER)", f"{usdc_dispo:.2f} $", delta=f"{prix_actuel:.4f} $", delta_color="normal")

    st.divider()

    # --- CALCUL VOLUME (Divisé par 3 sur le TOTAL de 48$) ---
    vol_auto = round((usdc_total * 0.95 / 3) / prix_actuel, 1)

    # --- LES 3 BOITES (DÉFILANTES) ---
    prices_in = [1.3600, 1.3400, 1.3200]
    for i in range(3):
        p_idx = i + 1
        with st.expander(f"🚜 BOT {p_idx} - CONFIGURATION", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            p_in = st.number_input(f"ACHAT {p_idx}", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE {p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")
            
            st.write(f"📦 Volume prévu : **{vol_auto} XRP**")
            
            cl, cs = st.columns(2)
            if cl.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo > 13.5:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': round(p_out, 4)}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_auto, round(p_in, 4), params)
                    st.success("C'est parti !")
                    st.balloons()
                else: st.error("Solde Dispo trop petit")
            
            if cs.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
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
            couleur = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{couleur} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")
    else: st.write("Aucune mission active.")

    if st.button("🚨 RESET TOTAL (POUR RECHARGER LES 17$)", use_container_width=True):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
🎯 BUY 13.8 XRP @ 1.36 $
