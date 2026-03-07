import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DU PROFIT
if 'profit_reel' not in st.session_state:
    st.session_state.profit_reel = 0.0

# STYLE PREMIUM
st.set_page_config(page_title="XRP Sniper Live", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .profit-box { background: #28a745; color: white; padding: 15px; border-radius: 20px; text-align: center; margin-bottom: 10px; }
    .status-box { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 15px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; }
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

    # HEADER PROFIT & CAPITAL
    st.markdown(f'<div class="profit-box"><p style="margin:0; opacity:0.8;">PROFIT RÉEL ENCAISSÉ</p><h1>+ {st.session_state.profit_reel:.2f} $</h1></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box"><p style="margin:0; color:grey;">CAPITAL TOTAL KRAKEN</p><h2>{usdc_total:.2f} $</h2></div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    col_a.metric("LIBRE (POUR LANCER)", f"{usdc_dispo:.2f} $")
    col_b.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. RÉCUPÉRATION DES ORDRES POUR AFFICHAGE DYNAMIQUE
    orders = kraken.fetch_open_orders('XRP/USDC')
    prices_in = [1.3600, 1.3400, 1.3200]

    # 4. AFFICHAGE DES 3 BOTS AVEC MONTANT DYNAMIQUE
    for i in range(3):
        p_idx = i + 1
        p_cible = prices_in[i]
        
        # On cherche si un ordre existe pour ce prix pour afficher son montant
        montant_bot = 0.0
        for o in orders:
            if float(o['price']) == p_cible:
                montant_bot = float(o['amount']) * float(o['price'])
        
        label_montant = f" | 📦 {montant_bot:.2f} $" if montant_bot > 0 else " | 😴 Inactif"
        
        with st.expander(f"🚜 BOT {p_idx}{label_montant}", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            p_in = st.number_input(f"ACHAT", value=p_cible, format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")
            
            cl, cs = st.columns(2)
            if cl.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                # On utilise tout le solde DISPO si on lance, ou une part égale
                vol = round((usdc_dispo * 0.95) / p_in, 1)
                if vol >= 10:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success(f"B{p_idx} envoyé !")
                    st.rerun()
                else: st.error("Solde < 14$")
            
            if cs.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                for o in orders:
                    if float(o['price']) == p_in: kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # 5. MISSIONS RÉELLES
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES")
    if orders:
        for o in orders:
            couleur = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{couleur} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
