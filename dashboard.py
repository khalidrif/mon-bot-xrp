import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM (Mode Auto-Compound)
st.set_page_config(page_title="XRP Auto-Compounder", layout="centered")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    .status-box { background: #28a745; color: white; padding: 20px; border-radius: 25px; text-align: center; margin-bottom: 20px; box-shadow: 0px 10px 20px rgba(40, 167, 69, 0.1); }
    .info-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; text-align: center; }
    .stMetric { background: white; padding: 10px; border-radius: 15px; border: 1px solid #EEE; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION SÉCURISÉE
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    
    # SCAN DES FONDS (Tes 17$ + les retours de ventes)
    balance = kraken.fetch_balance()
    usdc_libre = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # HEADER : SOLDE LIBRE (L'argent qui attend de travailler)
    st.markdown(f'<div class="status-box"><p style="margin:0; opacity:0.8;">USDC PRÊT À INVESTIR</p><h1>{usdc_libre:.2f} $</h1></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("PRIX XRP LIVE", f"{prix_actuel:.4f} $")
    c2.metric("SOLDE TOTAL KRAKEN", f"{balance['total'].get('USDC', 0.0):.2f} $")

    st.divider()

    # --- LE CERVEAU AUTO-SCAN & RECHARGE ---
    # Si le solde libre > 14$ (Dépôt de 17$ détecté OU Vente d'un bot terminée)
    if usdc_libre > 14.0:
        st.info("🔄 Analyse des fonds détectés... Lancement automatique en cours.")
        
        # 1. On choisit la cible d'achat (On évite d'acheter trop haut)
        # On vise 1.3600 par défaut, ou 1.3400 si le prix est déjà plus bas
        cible_achat = 1.3600
        if prix_actuel < 1.3600:
            cible_achat = 1.3400
        
        # 2. ARRONDIS STRICTS (Pour éviter l'erreur Kraken 5 decimals)
        p_achat = round(cible_achat, 4)
        p_vente = round(p_achat + 0.02, 4)
        # Volume de XRP (on arrondit à 1 décimale, ex: 25.4)
        vol_total = round((usdc_libre * 0.96) / p_achat, 1)
        
        # 3. ACTION : On lance l'achat + la revente automatique
        try:
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_vente}}
            kraken.create_limit_buy_order('XRP/USDC', vol_total, p_achat, params)
            
            st.balloons()
            st.success(f"🤖 AUTO-INJECTION RÉUSSIE : {vol_total} XRP placés à {p_achat}$")
            time.sleep(2)
            st.rerun() # Rafraîchir pour voir la mission s'afficher
        except Exception as e_kraken:
            st.error(f"Erreur Kraken : {e_kraken}")

    # --- AFFICHAGE DES MISSIONS ACTIVES ---
    st.markdown("### 📦 MISSIONS EN COURS (KRAKEN)")
    orders = kraken.fetch_open_orders('XRP/USDC')
    if orders:
        for o in orders:
            couleur = "🎯" if o['side'] == 'buy' else "💰"
            st.info(f"{couleur} {o['side'].upper()} {o['amount']} XRP @ {o['price']} $")
    else:
        st.write("Aucune mission active. En attente de fonds (virement ou vente).")

    # BOUTON PANIQUE
    st.write("")
    if st.button("🚨 ARRÊT D'URGENCE / TOUT ANNULER", use_container_width=True):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"⚠️ Erreur de connexion : {e}")
    st.info("Vérification dans 60 secondes...")

# 3. SCAN TOUTES LES 60 SECONDES (Anti-Rate Limit)
time.sleep(60)
st.rerun()
