import streamlit as st
import pandas as pd
import ccxt
from config import get_kraken_connection
import time
import datetime

# 1. CONFIGURATION ET STYLE
st.set_page_config(page_title="Kraken Loop Bot Pro", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #0E2F56; border: 2px solid #007BFF; padding: 20px; border-radius: 15px; }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; font-size: 18px !important; }
    [data-testid="stMetricValue"] { color: #00FFCC !important; font-size: 35px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- MÉMOIRE DU BOT (Session State) ---
if 'etape_bot' not in st.session_state:
    st.session_state.etape_bot = "ATTENTE_ACHAT" 
if 'last_balance_update' not in st.session_state:
    st.session_state.last_balance_update = 0
    st.session_state.cached_balance = {}

# Connexion via ton fichier config.py
kraken = get_kraken_connection()

# --- BARRE LATÉRALE (RÉGLAGES) ---
with st.sidebar:
    st.header("🤖 Contrôle du Cycle")
    bot_actif = st.toggle("ACTIVER LE BOT", value=False)
    mode_reel = st.toggle("💰 PASSER EN ARGENT RÉEL", value=False)
    
    st.divider()
    p_achat = st.number_input("1. Prix d'Achat Cible ($)", value=1.3500, format="%.4f")
    p_vente = st.number_input("2. Prix de Vente Cible ($)", value=1.5000, format="%.4f")
    budget = st.number_input("Budget par achat (USDC)", min_value=25.0, value=30.0)

    if st.button("Réinitialiser Cycle (vers Achat)"):
        st.session_state.etape_bot = "ATTENTE_ACHAT"
        st.rerun()

st.title("📈 Terminal de Trading : Cycle Achat/Vente")

zone_live = st.empty()

# --- BOUCLE DE TRADING ---
while True:
    try:
        # 1. RÉCUPÉRATION DU PRIX (Correction cruciale [0][0])
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        
        # On extrait le PREMIER PRIX de la PREMIÈRE OFFRE
        prix_ask = float(ob['asks'][0][0])  # Prix pour acheter
        prix_bid = float(ob['bids'][0][0])  # Prix pour vendre
        prix_reel = (prix_ask + prix_bid) / 2
        
        # 2. RÉCUPÉRATION DU SOLDE (Toutes les 30s)
        maintenant = time.time()
        if maintenant - st.session_state.last_balance_update > 30:
            st.session_state.cached_balance = kraken.fetch_balance()
            st.session_state.last_balance_update = maintenant
        
        balance = st.session_state.cached_balance
        usdc_libre = balance.get('free', {}).get('USDC', 0)
        xrp_libre = balance.get('free', {}).get('XRP', 0)

        with zone_live.container():
            # Affichage du statut du cycle
            couleur_etat = "blue" if st.session_state.etape_bot == "ATTENTE_ACHAT" else "orange"
            st.subheader(f"🔄 État du Bot : :{couleur_etat}[{st.session_state.etape_bot}]")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("USDC DISPO", f"{usdc_libre:,.2f} $")
            c2.metric("XRP DISPO", f"{xrp_libre:,.2f}")
            c3.metric("PRIX XRP (MOYEN)", f"{prix_reel:.4f} $")

            if bot_actif:
                if not mode_reel:
                    st.info("🧪 Mode Simulation : Les ordres ne sont pas réellement exécutés.")
                
                # --- ÉTAPE 1 : CHERCHE À ACHETER ---
                if st.session_state.etape_bot == "ATTENTE_ACHAT":
                    if prix_reel <= p_achat and usdc_libre >= budget:
                        qty = budget / prix_ask 
                        st.toast("🚀 Condition d'achat remplie !")
                        
                        # EXECUTION (validate: True si mode_reel est False)
                        kraken.create_order('XRP/USDC', 'market', 'buy', qty, params={'validate': not mode_reel})
                        
                        st.success(f"✅ ACHAT EFFECTUÉ ({qty:.2f} XRP) ! Passage à la vente...")
                        st.session_state.etape_bot = "ATTENTE_VENTE"
                        st.session_state.last_balance_update = 0 # Force refresh balance
                        time.sleep(15)
                
                # --- ÉTAPE 2 : CHERCHE À VENDRE ---
                elif st.session_state.etape_bot == "ATTENTE_VENTE":
                    # On vend si le prix monte ET qu'on a au moins 15 XRP (Minimum Kraken)
                    if prix_reel >= p_vente and xrp_libre >= 15:
                        st.toast("💰 Condition de vente remplie !")
                        
                        # EXECUTION
                        kraken.create_order('XRP/USDC', 'market', 'sell', xrp_libre, params={'validate': not mode_reel})
                        
                        st.success(f"✅ VENTE EFFECTUÉE ({xrp_libre:.2f} XRP) ! Retour à l'achat...")
                        st.session_state.etape_bot = "ATTENTE_ACHAT"
                        st.session_state.last_balance_update = 0
                        time.sleep(15)
                
                else:
                    st.write("⌛ Le bot guette le marché pour l'étape en cours...")

            st.divider()
            st.write(f"⏱️ Dernière mise à jour Kraken : {datetime.datetime.now().strftime('%H:%M:%S')}")

    except Exception as e:
        st.error(f"Erreur flux : {e}")
        time.sleep(10)

    # Pause de 10 secondes pour éviter le blocage API (Rate Limit)
    time.sleep(10)
