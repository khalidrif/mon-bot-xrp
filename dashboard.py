import streamlit as st
import ccxt
import time

# Configuration de la page iPhone
st.set_page_config(page_title="XRP Sniper Manuel", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .status-box { background: white; padding: 15px; border-radius: 15px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; height: 45px; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. CONNEXION KRAKEN (SÉCURISÉE AVEC NONCE)
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    # Lecture du compte
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    # HEADER SIMPLE
    st.markdown(f'<div class="status-box">🔵 SOLDE LIBRE : <b>{usdc_dispo:.2f} $</b></div>', unsafe_allow_html=True)
    st.divider()

    # 2. LES 4 BOTS (ZÉRO AUTOMATISME)
    # Chaque bot est un "tiroir" indépendant
    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = prices_in[i]
        
        # DÉTECTION : On regarde si un ordre existe à ce prix chez Kraken
        # Le voyant est VERT seulement s'il y a une mission réelle
        mission_active = any(abs(float(o['price']) - p_base) < 0.05 for o in orders)
        status_txt = "🟢 EN MISSION" if mission_active else "⚪ À L'ARRÊT"
        
        with st.expander(f"🚜 BOT {p_idx} | {status_txt}"):
            # Réglages modifiables
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"PRIX ACHAT B{p_idx}", value=p_base, format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"PRIX VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            col_l, col_s = st.columns(2)
            
            # BOUTON LANCER : Envoie l'ordre d'achat avec vente liée
            if col_l.button(f"🚀 LANCER", key=f"run{i}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    # Paramètre 'close' pour que Kraken pose la vente dès que l'achat réussit
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success("Mission envoyée !")
                    time.sleep(2)
                    st.rerun()

            # BOUTON STOP : Annule l'ordre et ne fait plus rien
            if col_s.button(f"🗑️ STOP", key=f"stop{i}"):
                for o in orders:
                    p_o = float(o['price'])
                    # Annule si le prix correspond à l'achat ou à la vente configurés
                    if abs(p_o - p_in) < 0.05 or abs(p_o - p_out) < 0.05:
                        kraken.cancel_order(o['id'])
                st.warning("Mission annulée.")
                time.sleep(1)
                st.rerun()

    # 3. LA VÉRITÉ DU COMPTE (LISTE DES ORDRES)
    st.divider()
    st.write("### 📦 TES MISSIONS SUR KRAKEN")
    if orders:
        for o in orders:
            type_o = "🎯 ACHAT" if o['side'] == 'buy' else "💰 VENTE"
            st.info(f"{type_o} {o['amount']} XRP @ {o['price']} $")
    else:
        st.write("Aucun ordre en cours.")

except Exception as e:
    st.error(f"Erreur Kraken : {e}")

# Rafraîchissement automatique toutes les 60s
time.sleep(60)
st.rerun()
