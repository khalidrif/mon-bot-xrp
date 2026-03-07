import streamlit as st
import ccxt
import time

# 1. STYLE PREMIUM IPHONE
st.set_page_config(page_title="XRP Sniper Pro", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .status-box { background: #28a745; color: white; padding: 20px; border-radius: 25px; text-align: center; margin-bottom: 20px; box-shadow: 0px 10px 20px rgba(40,167,69,0.15); }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 12px !important; font-weight: bold; height: 45px; background-color: #F3BA2F !important; color: black !important; }
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

    # HEADER : SCAN DU CAPITAL
    st.markdown(f'<div class="status-box"><p style="margin:0; opacity:0.8;">CAPITAL TOTAL KRAKEN</p><h1>{usdc_total:.2f} $</h1></div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    col_a.metric("LIBRE (SCAN)", f"{usdc_libre:.2f} $")
    col_b.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # --- CONFIGURATION DES 3 NIVEAUX ---
    prices_in = [1.3600, 1.3400, 1.3200]
    
    # 3. LE CERVEAU "INJECTION PROCHE"
    # Si le solde libre > 14$ (Dépôt ou Vente), on injecte sur le bot le plus haut
    if usdc_libre > 14.0:
        cible_proche = max(prices_in) # On choisit le prix le plus haut (le plus proche du marché)
        vol_renfort = round((usdc_libre * 0.96) / cible_proche, 1)
        p_vente = round(cible_proche + 0.02, 4)
        
        try:
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_vente}}
            kraken.create_limit_buy_order('XRP/USDC', vol_renfort, cible_proche, params)
            st.balloons()
            st.success(f"🚀 INJECTION AUTO : {vol_renfort} XRP ajoutés à {cible_proche}$")
            time.sleep(2)
            st.rerun()
        except Exception as e_k:
            st.error(f"Erreur Injection : {e_k}")

    # --- AFFICHAGE DES DOSSIERS BOTS ---
    for i in range(3):
        with st.expander(f"🚜 CONFIGURATION BOT {i+1}", expanded=(i==0)):
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            p_in = st.number_input(f"PRIX ACHAT", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"PRIX VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")
            
            # Bouton Manuel au cas où
            if st.button(f"🚀 LANCER MANUEL B{i+1}", key=f"btn{i}"):
                vol_man = round((usdc_libre * 0.95) / p_in, 1)
                if vol_man >= 10:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_man, p_in, params)
                    st.success("OK")
                else: st.error("Solde < 14$")
            st.markdown("</div>", unsafe_allow_html=True)

    # 4. MISSIONS RÉELLES
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES (KRAKEN)")
    orders = kraken.fetch_open_orders('XRP/USDC')
    if orders:
        for o in orders:
            couleur = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{couleur} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")
    else:
        st.write("Aucun ordre. En attente de fonds ou de prix.")

    if st.button("🚨 TOUT ANNULER / RESET"):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

# SCAN TOUTES LES 60 SECONDES
time.sleep(60)
st.rerun()
