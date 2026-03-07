import streamlit as st
import ccxt
import time

# 1. CONFIGURATION INTERFACE IPHONE
st.set_page_config(page_title="XRP Sniper Master V3", layout="centered")

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

    st.write(f"### 🔵 SOLDE LIBRE : {usdc_dispo:.2f} $")
    st.divider()

    # PRIX CIBLES FIXES (POUR SÉPARER B1, B2, B3, B4)
    # On réduit la marge de détection à 0.005 pour éviter les mélanges
    target_prices = [1.3650, 1.3400, 1.3200, 1.3000]

    for i in range(4):
        p_idx = i + 1
        p_base = target_prices[i]
        
        # --- DÉTECTION CHIRURGICALE (SÉPARE B2 DE B3) ---
        mission_active = False
        montant_engage = 0.0
        
        # On définit le prix d'achat et de vente de ce bot précis
        p_in_current = p_base
        p_out_current = round(p_base + 0.02, 4)

        for o in orders:
            p_o = float(o['price'])
            # Le bot ne s'allume QUE s'il voit son propre prix EXACT (marge ultra-fine)
            if abs(p_o - p_in_current) < 0.0005 or abs(p_o - p_out_current) < 0.0005:
                mission_active = True
                montant_engage = float(o['amount']) * p_o
                break

        # TITRE DYNAMIQUE UNIQUE (Identifie bien le BOT)
        if mission_active:
            titre = f"🟢 EN MISSION | {montant_engage:.2f} $ | BOT {p_idx}"
        else:
            titre = f"⚪ À L'ARRÊT | BOT {p_idx}"

        # Clé unique pour chaque expander pour éviter les conflits Streamlit
        with st.expander(titre, expanded=(i==0)):
            m_invest = st.number_input(f"MONTANT $ B{p_idx}", value=14.5, min_value=14.0, key=f"m{p_idx}")
            p_in = st.number_input(f"ACHAT B{p_idx}", value=p_in_current, format="%.4f", key=f"in{p_idx}")
            p_out = st.number_input(f"VENTE B{p_idx}", value=p_out_current, format="%.4f", key=f"out{p_idx}")

            c1, c2 = st.columns(2)
            if c1.button(f"🚀 LANCER B{p_idx}", key=f"run{p_idx}"):
                if usdc_dispo >= m_invest:
                    vol = round(m_invest / p_in, 1)
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
                    st.rerun()

            if c2.button(f"🗑️ STOP B{p_idx}", key=f"stop{p_idx}"):
                for o in orders:
                    p_o = float(o['price'])
                    # On annule seulement ce qui appartient à CE bot précis
                    if abs(p_o - p_in) < 0.0005 or abs(p_o - p_out) < 0.0005:
                        kraken.cancel_order(o['id'])
                st.rerun()

    # LISTE RÉELLE DES MISSIONS (LA VÉRITÉ KRAKEN)
    st.divider()
    st.write("### 📦 MISSIONS ACTIVES SUR KRAKEN")
    if orders:
        for o in orders:
            side = "🎯 ACHAT" if o['side'] == 'buy' else "💰 VENTE"
            st.info(f"{side} {o['amount']} XRP @ {o['price']} $")
    else:
        st.write("Aucune mission active.")

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(60)
st.rerun()
