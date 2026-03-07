import streamlit as st
import ccxt
import time

# 1. MÉMOIRE DES PROFITS, CYCLES ET ÉTATS
if 'profit_reel' not in st.session_state: st.session_state.profit_reel = 0.0
if 'cycles' not in st.session_state: st.session_state.cycles = {1:0, 2:0, 3:0, 4:0}
if 'bot_active' not in st.session_state: st.session_state.bot_active = {1:False, 2:False, 3:False, 4:False}
if 'last_click' not in st.session_state: st.session_state.last_click = 0

st.set_page_config(page_title="XRP Sniper Master", layout="centered")

try:
    # 2. CONNEXION KRAKEN AVEC FIX NONCE (ANTI-ERREUR)
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: str(int(time.time() * 1000))}
    })
    
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])
    balance = kraken.fetch_balance()
    usdc_dispo = balance['free'].get('USDC', 0.0)
    usdc_total = balance['total'].get('USDC', 0.0)
    orders = kraken.fetch_open_orders('XRP/USDC')

    # HEADER
    st.markdown(f"### 💰 PROFIT : {st.session_state.profit_reel:.2f} $ | 🔵 LIBRE : {usdc_dispo:.2f} $")
    st.write(f"📊 **CAPITAL : {usdc_total:.2f} $** | **PRIX XRP : {prix_actuel:.4f} $**")
    st.divider()

    # 3. LES 4 BOTS (DÉTECTION PAR MONTANT)
    prices_in = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        with st.container():
            # RÉGLAGES PAR BOT
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{i}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")

            # --- DÉTECTION VISUELLE ---
            # Le bot s'allume s'il voit un ordre qui fait environ son montant ($)
            is_on_kraken = False
            for o in orders:
                valeur_usd = float(o['amount']) * float(o['price'])
                if abs(valeur_usd - m_invest) < 0.6: # Marge souple
                    is_on_kraken = True
                    break

            statut = "🟢 ACTIF" if is_on_kraken else "⚪ INACTIF"
            label_head = f"🚜 BOT {p_idx} | {statut} | 🔄 {st.session_state.cycles[p_idx]} Cycles"

            with st.expander(label_head, expanded=(i==0)):
                # BOULE DE NEIGE AUTOMATIQUE
                if st.session_state.bot_active[p_idx] and not is_on_kraken and usdc_dispo >= m_invest:
                    st.session_state.profit_reel += (p_out - p_in) * (m_invest / p_in)
                    st.session_state.cycles[p_idx] += 1
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

                col_l, col_s = st.columns(2)
                # LANCER (Avec protection 5s)
                if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
                    if time.time() - st.session_state.last_click > 5 and usdc_dispo >= m_invest:
                        st.session_state.last_click = time.time()
                        st.session_state.bot_active[p_idx] = True
                        vol = round(m_invest / p_in, 1)
                        params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                        kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                        st.rerun()

                # STOP (Annule l'ordre par son montant)
                if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
                    st.session_state.bot_active[p_idx] = False
                    for o in orders:
                        val_o = float(o['amount']) * float(o['price'])
                        if abs(val_o - m_invest) < 0.6:
                            kraken.cancel_order(o['id'])
                    st.rerun()

    # MISSIONS RÉELLES
    st.divider()
    st.write("### 📦 MISSIONS SUR KRAKEN")
    for o in orders:
        ico = "🎯" if o['side'] == 'buy' else "💰"
        st.info(f"{ico} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
