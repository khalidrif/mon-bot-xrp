import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES BOTS ACTIFS (Pour éviter les doublons)
if 'active_bots' not in st.session_state:
    st.session_state.active_bots = {} # On stocke les IDs des ordres lancés

st.set_page_config(page_title="XRP Snowball Sniper", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); }
    .status-box { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 15px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; height: 45px; }
    </style>
    """, unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # HEADER
    st.markdown(f'<div class="status-box"><h2>SOLDE LIBRE : {usdc_dispo:.2f} $</h2><p>PRIX XRP : {prix_actuel:.4f} $</p></div>', unsafe_allow_html=True)

    prices_in = [1.3600, 1.3400, 1.3200]
    orders = kraken.fetch_open_orders('XRP/USDC')

    for i in range(3):
        p_idx = i + 1
        p_cible = prices_in[i]
        
        # On vérifie si un ordre existe DEJA sur Kraken pour ce prix exact
        deja_en_cours = any(float(o['price']) == p_cible for o in orders)
        status = "🟢 BOULE DE NEIGE" if deja_en_cours else "⚪ INACTIF"
        
        with st.expander(f"🚜 BOT {p_idx} | {status}", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            
            m_invest = st.number_input("MONTANT $", value=15.0, min_value=14.0, key=f"m{i}")
            p_in = st.number_input("PRIX ACHAT", value=p_cible, format="%.4f", key=f"in{i}")
            p_out = st.number_input("PRIX VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # --- LOGIQUE BOULE DE NEIGE AUTOMATIQUE ---
            # Si le bot a fini sa vente (plus d'ordre sur Kraken) mais qu'on l'avait activé
            if p_idx in st.session_state.active_bots and not deja_en_cours:
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.toast(f"❄️ Boule de neige B{p_idx} relancée !")
                    time.sleep(1)
                    st.rerun()

            col_l, col_s = st.columns(2)
            
            # LANCER : Crée l'ordre ET active la mémoire pour la suite
            if col_l.button(f"🚀 LANCER", key=f"run{i}"):
                if not deja_en_cours and usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.session_state.active_bots[p_idx] = True # On active la mémoire
                    st.success("Premier achat lancé !")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Déjà actif ou solde insuffisant")

            # STOP : Annule et vide la mémoire (arrête la boule de neige)
            if col_s.button(f"🗑️ STOP", key=f"stop{i}"):
                if p_idx in st.session_state.active_bots:
                    del st.session_state.active_bots[p_idx] # On vide la mémoire
                for o in orders:
                    if float(o['price']) == p_in:
                        kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # MISSIONS
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES")
    if orders:
        for o in orders:
            ico = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

    if st.button("🚨 RESET TOTAL (STOP TOUT)"):
        st.session_state.active_bots = {}
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
