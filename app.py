import streamlit as st
import pandas as pd
import ccxt
from config import get_kraken_connection
import time
import datetime

# 1. STYLE VISUEL BLEU PRO (STABLE)
st.set_page_config(page_title="XRP Auto-Bot Pro", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #0E2F56; 
        border: 2px solid #007BFF; 
        padding: 20px;
        border-radius: 15px;
    }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; font-size: 18px !important; }
    [data-testid="stMetricValue"] { color: #00FFCC !important; font-size: 35px !important; }
    /* Fixe l'interface pour éviter la vague */
    .main { background-color: #F0F2F6; }
    </style>
    """, unsafe_allow_html=True)

# Connexion Kraken
kraken = get_kraken_connection()

# Initialisation Session State
if 'last_balance_update' not in st.session_state:
    st.session_state.last_balance_update = 0
    st.session_state.cached_balance = {}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🤖 Robot de Trading")
    bot_actif = st.toggle("ACTIVER LE BOT", value=False)
    st.divider()
    # Tes cibles : ex Achat 1.50 / Vente 1.60
    p_achat_cible = st.number_input("ACHAT SI PRIX <", value=1.5000, format="%.4f")
    p_vente_cible = st.number_input("VENTE SI PRIX >", value=1.6000, format="%.4f")
    budget_usdc = st.number_input("Budget Achat (USDC)", min_value=10.0, value=30.0)

# Zone d'affichage fixe (Anti-vague)
zone_live = st.empty()

while True:
    try:
        # --- PARTIE PRIX (NE PAS TOUCHER - FONCTIONNE) ---
        params = {'nonce': str(int(time.time() * 1000))}
        ticker = kraken.fetch_ticker('XRP/USDC', params=params)
        prix_reel = ticker['last']
        
        # --- PARTIE SOLDE (TOUTES LES 30S) ---
        maintenant = time.time()
        if maintenant - st.session_state.last_balance_update > 30:
            st.session_state.cached_balance = kraken.fetch_balance()
            st.session_state.last_balance_update = maintenant
        
        balance = st.session_state.cached_balance
        usdc_libre = balance.get('free', {}).get('USDC', 0)
        xrp_libre = balance.get('free', {}).get('XRP', 0)
        
        # --- AFFICHAGE DASHBOARD ---
        with zone_live.container():
            st.title("📈 Terminal XRP - Mode Automatique")
            c1, c2, c3 = st.columns(3)
            c1.metric("PORTFOLIO USDC", f"{usdc_libre:,.2f} $")
            c2.metric("STOCK XRP", f"{xrp_libre:,.2f}")
            c3.metric("PRIX XRP LIVE", f"{prix_reel:.4f} $")

            st.write(f"⏱️ Flux Kraken : **{datetime.datetime.now().strftime('%H:%M:%S')}**")
            
            # --- LOGIQUE ACHAT / VENTE (1.5 / 1.6) ---
            if bot_actif:
                st.info(f"🕵️ Stratégie : ACHAT à {p_achat_cible}$ | VENTE à {p_vente_cible}$")
                
                # 1. LOGIQUE ACHAT (On a des dollars -> On veut du XRP)
                if prix_reel <= p_achat_cible and usdc_libre >= budget_usdc:
                    try:
                        st.toast("🚀 CONDITION ACHAT REMPLIE !")
                        # Calcul quantité avec précision Kraken
                        qty = float(kraken.amount_to_precision('XRP/USDC', budget_usdc / prix_reel))
                        px = float(kraken.price_to_precision('XRP/USDC', p_achat_cible))
                        
                        # Ordre Limite pour garantir le prix
                        res = kraken.create_order('XRP/USDC', 'limit', 'buy', qty, px)
                        st.success(f"✅ BOT : Ordre Achat placé ({qty} XRP à {px}$)")
                        st.session_state.last_balance_update = 0 # Force refresh solde
                        time.sleep(15)
                    except Exception as e:
                        st.error(f"Erreur Achat : {e}")
                
                # 2. LOGIQUE VENTE (On a du XRP -> On veut du profit)
                elif prix_reel >= p_vente_cible and xrp_libre >= 15:
                    try:
                        st.toast("💰 CONDITION VENTE REMPLIE !")
                        qty = float(kraken.amount_to_precision('XRP/USDC', xrp_libre))
                        px = float(kraken.price_to_precision('XRP/USDC', p_vente_cible))
                        
                        res = kraken.create_order('XRP/USDC', 'limit', 'sell', qty, px)
                        st.success(f"✅ BOT : Ordre Vente placé ({qty} XRP à {px}$)")
                        st.session_state.last_balance_update = 0
                        time.sleep(15)
                    except Exception as e:
                        st.error(f"Erreur Vente : {e}")
                else:
                    st.write("⌛ *En attente des cibles de prix...*")

            st.divider()
            st.subheader("📝 Mes Avoirs")
            df = pd.DataFrame(balance.get('total', {}).items(), columns=['Actif', 'Total'])
            st.table(df[df['Total'] > 0].reset_index(drop=True))

    except Exception as e:
        st.error(f"Erreur Système : {e}")
        time.sleep(10)

    # Pause entre deux scans (10s pour la stabilité)
    time.sleep(10)
