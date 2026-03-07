import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# Configuration de la page Pro
st.set_page_config(page_title="Kraken XRP Algo-Trader", layout="wide", page_icon="📈")

# Style CSS personnalisé pour un look "Dark Mode Professional"
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4255; }
    .bot-card { padding: 20px; border-radius: 15px; border-left: 5px solid #00ffcc; background-color: #161b22; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNEXION KRAKEN ---
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })

try:
    exchange = get_exchange()
    balance = exchange.fetch_balance()
    xrp_bal = balance['total'].get('XRP', 0)
    usdc_bal = balance['total'].get('USDC', 0)
except Exception as e:
    st.error(f"Erreur de connexion API : {e}")
    st.stop()

# --- HEADER & PORTFOLIO ---
st.title("📈 Kraken XRP Professional Grid")
col_bal1, col_bal2, col_bal3, col_bal4 = st.columns(4)
with col_bal1: st.metric("Solde XRP", f"{xrp_bal:,.2f} XRP")
with col_bal2: st.metric("Solde USDC", f"{usdc_bal:,.2f} USDC")
with col_bal3: 
    ticker = exchange.fetch_ticker('XRP/USDC')
    st.metric("Prix XRP/USDC", f"{ticker['last']:.4f}", f"{ticker['percentage']:.2f}%")
with col_bal4: st.write(f"⏱️ {datetime.now().strftime('%H:%M:%S')}")

st.divider()

# --- CONFIGURATION DES BOTS ---
st.subheader("⚙️ Configuration des Lignes de Trading")
c1, c2 = st.columns(2)

with c1:
    st.markdown('<div class="bot-card"><h4>🤖 BOT LIGNE HAUTE</h4>', unsafe_allow_html=True)
    h_buy = st.number_input("Achat (Haut)", value=2.450, format="%.3f", key="hb")
    h_sell = st.number_input("Vente (Haut)", value=2.550, format="%.3f", key="hs")
    h_qty = st.number_input("Quantité XRP (H)", value=20.0, key="hq")
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="bot-card" style="border-left-color: #ff4b4b;"><h4>🤖 BOT LIGNE BASSE</h4>', unsafe_allow_html=True)
    b_buy = st.number_input("Achat (Bas)", value=2.350, format="%.3f", key="bb")
    b_sell = st.number_input("Vente (Bas)", value=2.450, format="%.3f", key="bs")
    b_qty = st.number_input("Quantité XRP (B)", value=20.0, key="bq")
    st.markdown('</div>', unsafe_allow_html=True)

# --- CONTRÔLE ET LOGS ---
col_ctrl, col_logs = st.columns([1, 2])

with col_ctrl:
    st.write("### 🕹️ Contrôle")
    if 'active' not in st.session_state: st.session_state.active = False
    
    if st.button("▶️ DÉMARRER LA GRILLE", use_container_width=True, type="primary"):
        st.session_state.active = True
    
    if st.button("⏹️ ARRÊTER TOUT", use_container_width=True):
        st.session_state.active = False
        st.experimental_rerun()

with col_logs:
    st.write("### 📊 Activité en Temps Réel")
    log_h = st.empty()
    log_b = st.empty()

# --- LOGIQUE D'EXÉCUTION ---
if st.session_state.active:
    symbol = 'XRP/USDC'
    while st.session_state.active:
        # --- LOGIQUE BOT HAUT ---
        log_h.info(f"**Bot Haut** : En attente d'achat à **{h_buy}**...")
        # (Ici vous pouvez insérer le code réel exchange.create_order)
        
        # --- LOGIQUE BOT BAS ---
        log_b.info(f"**Bot Bas** : En attente d'achat à **{b_buy}**...")
        
        time.sleep(10) # Pause de sécurité pour l'API
        st.toast("Mise à jour des bots...")
