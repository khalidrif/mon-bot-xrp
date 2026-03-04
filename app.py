import streamlit as st
import pandas as pd
import ccxt
from config import get_kraken_connection
import time
import datetime

# 1. STYLE VISUEL BLEU PRO
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
    </style>
    """, unsafe_allow_html=True)

# Connexion via ton fichier config.py
kraken = get_kraken_connection()

# Initialisation de la mémoire du bot (Session State)
if 'last_balance_update' not in st.session_state:
    st.session_state.last_balance_update = 0
    st.session_state.cached_balance = {}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🤖 Robot de Trading")
    bot_actif = st.toggle("ACTIVER LE BOT", value=False)
    st.divider()
    seuil_achat = st.number_input("Acheter si <", value=1.3000, format="%.4f")
    seuil_vente = st.number_input("Vendre si >", value=1.5500, format="%.4f")
    budget_usdc = st.number_input("Budget Achat (USDC)", min_value=25.0, value=30.0)

st.title("📈 Terminal XRP - Flux Sécurisé")

# Zone de rafraîchissement
zone_live = st.empty()

while True:
    try:
        # 1. LECTURE DU PRIX (Toutes les 10s)
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        prix_bid = ob['bids'][0][0]
        prix_ask = ob['asks'][0][0]
        prix_reel = (prix_bid + prix_ask) / 2
        
        # 2. LECTURE DU SOLDE (Toutes les 30s pour éviter le BAN)
        maintenant = time.time()
        if maintenant - st.session_state.last_balance_update > 30:
            st.session_state.cached_balance = kraken.fetch_balance()
            st.session_state.last_balance_update = maintenant # <-- CORRIGÉ : signe = ajouté
        
        balance = st.session_state.cached_balance
        usdc_libre = balance.get('free', {}).get('USDC', 0)
        xrp_libre = balance.get('free', {}).get('XRP', 0)
        
        with zone_live.container():
            c1, c2, c3 = st.columns(3)
            c1.metric("PORTFOLIO USDC", f"{usdc_libre:,.2f} $")
            c2.metric("STOCK XRP", f"{xrp_libre:,.2f}")
            c3.metric("PRIX XRP LIVE", f"{prix_reel:.4f} $")

            st.write(f"⏱️ Flux Kraken : **{datetime.datetime.now().strftime('%H:%M:%S')}**")
            
            # --- LOGIQUE DU BOT ---
            if bot_actif:
                st.warning(f"🕵️ Surveillance : ACHAT < {seuil_achat}$ | VENTE > {seuil_vente}$")
                
                # ACHAT
                if prix_reel <= seuil_achat and usdc_libre >= budget_usdc:
                    st.toast("🚀 ACHAT DÉCLENCHÉ !")
                    qty = budget_usdc / prix_ask
                    res = kraken.create_order('XRP/USDC', 'market', 'buy', qty)
                    st.success(f"✅ BOT : Achat réussi (ID: {res['id']})")
                    st.session_state.last_balance_update = 0 # Force refresh solde au prochain tour
                    time.sleep(15)
                
                # VENTE
                elif prix_reel >= seuil_vente and xrp_libre >= 15:
                    st.toast("💰 VENTE DÉCLENCHÉE !")
                    res = kraken.create_order('XRP/USDC', 'market', 'sell', xrp_libre)
                    st.success(f"✅ BOT : Vente réussie (ID: {res['id']})")
                    st.session_state.last_balance_update = 0 # Force refresh solde
                    time.sleep(15)
                else:
                    st.info("⌛ En attente du bon prix...")

            st.divider()
            st.subheader("📝 Mes Avoirs")
            df = pd.DataFrame(balance.get('total', {}).items(), columns=['Actif', 'Total'])
            st.table(df[df['Total'] > 0].reset_index(drop=True))

    except Exception as e:
        if "Rate limit exceeded" in str(e):
            st.error("⚠️ Kraken saturé ! Pause de 30 secondes...")
            time.sleep(30)
        else:
            st.error(f"Erreur : {e}")
            time.sleep(10)

    # Pause de sécurité (10 secondes recommandée)
    time.sleep(10)
