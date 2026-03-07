import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES BOTS (Pour la Boule de Neige et éviter les doublons)
if 'active_bots' not in st.session_state:
    st.session_state.active_bots = {} 
if 'profit_reel' not in st.session_state:
    st.session_state.profit_reel = 0.0

st.set_page_config(page_title="XRP Sniper Snowball", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .profit-box { background: #28a745; color: white; padding: 15px; border-radius: 20px; text-align: center; margin-bottom: 10px; }
    .status-box { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; text-align: center; margin-bottom: 15px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; height: 45px; }
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

    # AFFICHAGE
    st.markdown(f'<div class="profit-box">PROFIT RÉEL : + {st.session_state.profit_reel:.2f} $</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box"><p style="margin:0; color:grey;">CAPITAL TOTAL</p><h2>{usdc_total:.2f} $</h2></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("LIBRE (USDC)", f"{usdc_dispo:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. INTERFACE 3 BOTS
    orders = kraken.fetch_open_orders('XRP/USDC')
    prices_in = [1.3600, 1.3400, 1.3200]

    for i in range(3):
        p_idx = i + 1
        p_cible = prices_in[i]
        
        # SÉCURITÉ : On vérifie si un ordre existe déjà sur Kraken à ce prix
        deja_en_cours = any(float(o['price']) == p_cible for o in orders)
        
        status = "🟢 BOULE DE NEIGE" if deja_en_cours else "⚪ INACTIF"
        
        with st.expander(f"🚜 BOT {p_idx} | {status}", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            
            m_invest = st.number_input("MONTANT $", value=15.0, min_value=14.0, key=f"m{i}")
            p_in = st.number_input("PRIX ACHAT", value=p_cible, format="%.4f", key=f"in{i}")
            p_out = st.number_input("PRIX VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # --- LOGIQUE BOULE DE NEIGE (Relance Auto) ---
            # Si le bot est activé dans la mémoire mais n'a plus d'ordre sur Kraken (vente finie)
            if p_idx in st.session_state.active_bots and not deja_en_cours:
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.toast(f"❄️ B{p_idx} relancé automatiquement !")
                    time.sleep(1)
                    st.rerun()

            col_l, col_s = st.columns(2)
            
            # BOUTON LANCER : 1 Clic = 1 Ordre + Active la Boule de Neige
            if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                if not deja_en_cours and usdc_dispo >= m_invest:
                    st.session_state.active_bots[p_idx] = True # On active la mémoire
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.success("Premier cycle lancé !")
                    time.sleep(1)
                    st.rerun()
                elif deja_en_cours:
                    st.warning("Un ordre est déjà actif à ce prix !")
                else:
                    st.error("Solde insuffisant")

            # BOUTON STOP : Arrête tout pour ce bot
            if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                if p_idx in st.session_state.active_bots:
                    del st.session_state.active_bots[p_idx] # On vide la mémoire
                for o in orders:
                    if float(o['price']) == p_in:
                        kraken.cancel_order(o['id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # 4. MISSIONS ACTIVES
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES SUR KRAKEN")
    if orders:
        for o in orders:
            ico = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")
    else:
        st.write("Aucune mission. Clique sur LANCER pour démarrer.")

    if st.button("🚨 RESET TOTAL (STOP TOUT)"):
        st.session_state.active_bots = {}
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
