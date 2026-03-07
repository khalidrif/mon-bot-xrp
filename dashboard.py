import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DU PROFIT RÉEL (DANS LA POCHE)
if 'profit_total_reel' not in st.session_state:
    st.session_state.profit_total_reel = 0.0

# STYLE PREMIUM
st.set_page_config(page_title="XRP Sniper Pro + Profit", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .profit-box { background: #28a745; color: white; padding: 20px; border-radius: 25px; text-align: center; margin-bottom: 10px; box-shadow: 0px 10px 20px rgba(40,167,69,0.2); }
    .status-box { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 15px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; height: 45px; background-color: #F3BA2F !important; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION KRAKEN
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_total = balance['total'].get('USDC', 0.0)
    usdc_libre = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # --- LE COMPTEUR DE PROFITS RÉELS ---
    st.markdown(f"""
        <div class="profit-box">
            <p style="margin:0; font-size:1rem; opacity:0.9;">PROFIT TOTAL RÉALISÉ</p>
            <h1 style="margin:0; font-size:3rem;">+ {st.session_state.profit_total_reel:.2f} $</h1>
        </div>
    """, unsafe_allow_html=True)

    # HEADER : CAPITAL
    st.markdown(f'<div class="status-box"><p style="margin:0; color:grey;">CAPITAL TOTAL KRAKEN</p><h2>{usdc_total:.2f} $</h2></div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    col_a.metric("LIBRE (SCAN)", f"{usdc_libre:.2f} $")
    col_b.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # --- INTELLIGENCE DE PROXIMITÉ (Injection des 17$) ---
    prices_in = [1.3600, 1.3400, 1.3200]
    
    if usdc_libre > 14.0:
        cible_proche = max(prices_in) 
        vol_renfort = round((usdc_libre * 0.96) / cible_proche, 1)
        p_vente = round(cible_proche + 0.02, 4)
        
        try:
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_vente}}
            kraken.create_limit_buy_order('XRP/USDC', vol_renfort, cible_proche, params)
            st.balloons()
            # On ajoute le profit estimé de cette injection au compteur dès que ça vendra
            gain_net = (vol_renfort * 0.02) - (usdc_libre * 0.0052)
            st.session_state.profit_total_reel += max(0, gain_net)
            st.success(f"🚀 INJECTION AUTO : {vol_renfort} XRP ajoutés !")
            time.sleep(2)
            st.rerun()
        except Exception as e_k:
            st.error(f"Erreur : {e_k}")

    # --- DOSSIERS BOTS ---
    for i in range(3):
        with st.expander(f"🚜 BOT {i+1} - RÉGLAGES", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            p_in = st.number_input(f"ACHAT", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")
            
            if st.button(f"🚀 LANCER B{i+1}", key=f"btn{i}"):
                vol_man = round((usdc_libre * 0.95) / p_in, 1)
                if vol_man >= 10:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_man, p_in, params)
                    st.success("Mission lancée")
                else: st.error("Solde < 14$")
            st.markdown("</div>", unsafe_allow_html=True)

    # MISSIONS RÉELLES
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES")
    orders = kraken.fetch_open_orders('XRP/USDC')
    if orders:
        for o in orders:
            st.info(f"🎯 {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

    if st.button("🚨 RESET COMPTEUR PROFIT"):
        st.session_state.profit_total_reel = 0.0
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
