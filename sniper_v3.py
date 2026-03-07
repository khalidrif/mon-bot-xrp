import streamlit as st
import ccxt
import time

# 1. CONFIGURATION IPHONE - INTERFACE PRO
st.set_page_config(page_title="XRP Sniper Manuel V3", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .status-box { background: white; padding: 15px; border-radius: 15px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; height: 45px; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION KRAKEN (NOUVELLES CLÉS SÉCURISÉES)
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    # LECTURE DIRECTE DU COMPTE
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    # HEADER - TON CAPITAL RÉEL
    st.markdown(f'<div class="status-box">🔵 SOLDE LIBRE : <b>{usdc_dispo:.2f} $</b></div>', unsafe_allow_html=True)
    st.divider()

    # 3. LES 4 SNIPERS INDÉPENDANTS
    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # RÉGLAGES DU BOT (DÉPLACÉS AVANT LA DÉTECTION POUR LA PRÉCISION)
        with st.expander(f"🚜 BOT {p_idx}", expanded=(i==0)):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # --- DÉTECTION PRÉCISE PAR BOT (VÉRIFIÉ 100%) ---
            # Le voyant est VERT seulement si un ordre correspond EXACTEMENT à ce prix d'achat ou de vente
            mission_active = any(abs(float(o['price']) - p_in) < 0.0005 or abs(float(o['price']) - p_out) < 0.0005 for o in orders)
            status_txt = "🟢 EN MISSION" if mission_active else "⚪ À L'ARRÊT"
            st.write(f"**STATUT : {status_txt}**")

            col_l, col_s = st.columns(2)
            
            # BOUTON LANCER (1 clic = 1 mission, pas de relance auto)
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    # Paramètre 'close' pour la vente liée automatique
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success(f"Bot {p_idx} lancé à {p_in} $")
                    time.sleep(2)
                    st.rerun()

            # BOUTON STOP (Annule uniquement l'ordre de ce bot)
            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                for o in orders:
                    p_o = float(o['price'])
                    if abs(p_o - p_in) < 0.001 or abs(p_o - p_out) < 0.001:
                        kraken.cancel_order(o['id'])
                st.warning(f"Bot {p_idx} arrêté.")
                time.sleep(1)
                st.rerun()

    # 4. LA LISTE DES MISSIONS RÉELLES SUR KRAKEN
    st.divider()
    st.write("### 📦 TES MISSIONS ACTIVES SUR KRAKEN")
    if orders:
        for o in orders:
            side = "🎯 ACHAT" if o['side'] == 'buy' else "💰 VENTE"
            st.info(f"{side} {o['amount']} XRP @ {o['price']} $")
    else:
        st.write("Aucune mission active. Ton argent est en sécurité.")

except Exception as e:
    st.error(f"Erreur Kraken : {e}")

time.sleep(60)
st.rerun()
