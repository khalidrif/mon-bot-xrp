import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES PROFITS ET ÉTATS
if 'profit_total' not in st.session_state: st.session_state.profit_total = 0.0
if 'bot_profits' not in st.session_state: st.session_state.bot_profits = {1:0.0, 2:0.0, 3:0.0, 4:0.0}
if 'cycles' not in st.session_state: st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
if 'bot_active' not in st.session_state: st.session_state.bot_active = {1:False, 2:False, 3:False, 4:False}

st.set_page_config(page_title="XRP SNIPER MASTER", layout="centered")

try:
    # 2. CONNEXION KRAKEN
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    # HEADER GÉANT
    st.write(f"## 💵 TOTAL : {st.session_state.profit_total:.4f} $")
    st.write(f"### 🔵 LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    # VOLUMES UNIQUES POUR SÉPARER B1, B2, B3, B4 (DÉTECTION PAR DÉFAUT)
    bot_vols_base = {1: 10.6, 2: 10.8, 3: 11.0, 4: 11.2}
    base_prices = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_in_default = base_prices[i]
        p_out_default = round(p_in_default + 0.02, 4)
        
        with st.expander(f"BOT {p_idx}", expanded=(p_idx==1)):
            # --- SAISIE DU MONTANT LIBRE ---
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.50, min_value=14.0, step=0.5, key=f"m{p_idx}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_in_default, format="%.4f", key=f"in{p_idx}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=p_out_default, format="%.4f", key=f"out{p_idx}")
            
            vol_calculé = round(m_invest / p_in, 1)

            # --- DÉTECTION POUR LA BARRE ---
            mission_active = False
            montant_reel = 0.0
            for o in orders:
                # Détection par prix pour permettre n'importe quel montant
                if abs(float(o['price']) - p_in) < 0.001 or abs(float(o['price']) - p_out) < 0.001:
                    mission_active = True
                    montant_reel = float(o['amount']) * float(o['price'])
                    break

            # TITRE DE LA BARRE (DYNAMIQUE)
            status = "🟢" if mission_active else "⚪"
            p_bot = st.session_state.bot_profits[p_idx]
            cyc = st.session_state.cycles[p_idx]
            profit_gras = f"{p_bot:.4f}".replace('0','𝟬').replace('1','𝟭').replace('2','𝟮').replace('3','𝟯').replace('4','𝟰').replace('5','𝟱').replace('6','𝟲').replace('7','𝟳').replace('8','𝟴').replace('9','𝟵')
            
            st.markdown(f"**{status} {montant_reel:.2f}$ | {p_in}➔{p_out} | 🔄 {cyc} | 💰 +{profit_gras}**")

            # BOULE DE NEIGE AUTO
            if st.session_state.bot_active[p_idx] and not mission_active and usdc_dispo >= m_invest:
                gain_net = (p_out - p_in) * vol_calculé
                st.session_state.profit_total += gain_net
                st.session_state.bot_profits[p_idx] += gain_net
                st.session_state.cycles[p_idx] += 1
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol_calculé, p_in, params)
                st.rerun()

            c1, c2 = st.columns(2)
            if c1.button(f"🚀 LANCER B{p_idx}", key=f"run{p_idx}"):
                st.session_state.bot_active[p_idx] = True
                if usdc_dispo >= m_invest:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_calculé, p_in, params)
                    st.rerun()

            if c2.button(f"🗑️ STOP B{p_idx}", key=f"stop{p_idx}"):
                st.session_state.bot_active[p_idx] = False
                for o in orders:
                    if abs(float(o['price']) - p_in) < 0.001 or abs(float(o['price']) - p_out) < 0.001:
                        kraken.cancel_order(o['id'])
                st.rerun()

    # MISSIONS RÉELLES
    st.divider()
    for o in orders:
        st.info(f"**{o['side'].upper()} {o['amount']} XRP @ {o['price']} $**")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
