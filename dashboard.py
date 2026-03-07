import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM (Auto-Scan Edition)
st.set_page_config(page_title="XRP Auto-Sniper", layout="wide")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); color: #212529; }
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] { color: #007AFF !important; font-size: 2rem !important; }
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] { color: #FF9500 !important; font-size: 2rem !important; }
    .cumul-box { background: linear-gradient(135deg, #28a745 0%, #218838 100%); border-radius: 20px; padding: 15px; text-align: center; color: white; margin-bottom: 10px; }
    .bot-card { background: white; padding: 15px; border-radius: 20px; border: 1px solid #DEE2E6; margin-bottom: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.03); }
    .stButton>button { width: 100%; height: 50px; border-radius: 15px !important; background-color: #F3BA2F !important; font-weight: bold; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 2. CONNEXION SÉCURISÉE (Anti-Rate Limit)
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True, # INDISPENSABLE pour ne pas être banni
    })
    
    # RÉCUPÉRATION DES DONNÉES
    balance = kraken.fetch_balance()
    usdc_total = balance['total'].get('USDC', 0.0)
    usdc_dispo = balance['free'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    # HEADER : SOLDE TOTAL (Scan le dépôt de 10$)
    st.markdown(f'<div class="cumul-box"><p style="margin:0; opacity:0.8;">SOLDE TOTAL KRAKEN</p><h1>{usdc_total:.2f} $</h1></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("LIBRE (POUR BOTS)", f"{usdc_dispo:.2f} $")
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. CALCUL AUTO DU VOLUME (Divisé par 3)
    # On utilise le solde TOTAL pour prévoir la puissance des 3 bots
    vol_auto = (usdc_total * 0.95 / 3) / prix_actuel

    # 4. INTERFACE DES 3 BOTS
    cols = st.columns(3)
    prices_in = [1.3600, 1.3400, 1.3200] # Valeurs par défaut
    
    for i in range(3):
        with cols[i]:
            st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
            st.subheader(f"🚜 BOT {i+1}")
            p_in = st.number_input(f"ACHAT", value=prices_in[i], format="%.4f", key=f"in{i}")
            p_out = st.number_input(f"VENTE", value=p_in + 0.02, format="%.4f", key=f"out{i}")
            
            if st.button(f"🚀 LANCER B{i+1}", key=f"btn{i}"):
                if usdc_dispo > 13.5:
                    params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                    kraken.create_limit_buy_order('XRP/USDC', vol_auto, p_in, params)
                    st.success(f"B{i+1} Lancé !")
                    st.balloons()
                else:
                    st.error("Solde Libre < 14$")
            st.markdown("</div>", unsafe_allow_html=True)

    # 5. LISTE DES MISSIONS RÉELLES
    st.divider()
    st.markdown("### 📦 MISSIONS ACTIVES (SUR KRAKEN)")
    orders = kraken.fetch_open_orders('XRP/USDC')
    if orders:
        for o in orders:
            st.info(f"🎯 {o['side'].upper()} {o['amount']:.1f} XRP @ {o['price']} $")
    else:
        st.write("Aucun ordre en attente.")

    # BOUTON PANIQUE / RECHARGE
    if st.button("🚨 TOUT ANNULER & RECHARGER LE SOLDE", use_container_width=True):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"⚠️ Erreur Kraken : {e}")
    st.info("Attends 1 minute sans rafraîchir la page (Rate Limit).")

# 6. PAUSE DE SÉCURITÉ (Scan toutes les 60 secondes)
time.sleep(60)
st.rerun()
