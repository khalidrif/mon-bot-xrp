import streamlit as st
import ccxt
import time

# 1. CONFIGURATION PRO
st.set_page_config(page_title="XRP Infinite Grid", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .status-box { background: #28a745; color: white; padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 10px; }
    .info-card { background: white; padding: 10px; border-radius: 15px; border: 1px solid #DEE2E6; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({'apiKey': st.secrets["KRAKEN_API_KEY"], 'secret': st.secrets["KRAKEN_SECRET"], 'enableRateLimit': True})
    
    # 2. SCAN DES FONDS (Tes 17$ + les retours de ventes)
    balance = kraken.fetch_balance()
    usdc_libre = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    st.markdown(f'<div class="status-box"><h1>SOLDE LIBRE : {usdc_libre:.2f} $</h1></div>', unsafe_allow_html=True)
    st.metric("PRIX XRP LIVE", f"{prix_actuel:.4f} $")

    st.divider()

    # --- LE CERVEAU AUTO-RECHARGE ---
    # Si le solde libre > 14$ (Dépôt détecté ou Vente terminée)
    if usdc_libre > 14.0:
        # On définit 3 niveaux cibles (tu peux les changer)
        cibles = [1.3600, 1.3400, 1.3200]
        
        # Le bot choisit la cible la plus proche du prix actuel mais en dessous
        cible_choisie = 1.3600 # Par défaut
        for c in cibles:
            if prix_actuel > c:
                cible_choisie = c
                break
        
        # On calcule le volume avec TOUT l'argent disponible (Scan + Vente)
        vol_final = (usdc_libre * 0.96) / cible_choisie
        p_vente = cible_choisie + 0.02
        
        # ACTION AUTOMATIQUE : On relance la mission
        params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_vente}}
        kraken.create_limit_buy_order('XRP/USDC', vol_final, cible_choisie, params)
        
        st.balloons()
        st.success(f"🤖 AUTO-RECHARGE : {vol_final:.1f} XRP envoyés à {cible_choisie}$")
        time.sleep(2)
        st.rerun()

    # 3. AFFICHAGE DES MISSIONS ACTIVES
    st.markdown("### 📦 MISSIONS EN COURS")
    orders = kraken.fetch_open_orders('XRP/USDC')
    if orders:
        for o in orders:
            st.info(f"🎯 {o['side'].upper()} {o['amount']:.1f} XRP @ {o['price']} $")
    else:
        st.write("En attente de fonds ou de prix bas...")

except Exception as e:
    st.error(f"Erreur : {e}")

# SCAN TOUTES LES 60 SECONDES
time.sleep(60)
st.rerun()
