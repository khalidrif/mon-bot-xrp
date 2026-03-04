import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# --- 1. STYLE FIXE ---
st.set_page_config(page_title="XRP Bloomberg Stable", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    [data-testid="stMetric"] { background-color: #FFFF00 !important; border-radius: 5px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 24px !important; font-weight: 900 !important; }
    .bot-line { border-bottom: 1px solid #222222; padding: 8px 0px; display: flex; justify-content: space-between; align-items: center; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 2px 6px; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INIT ---
FILE_MEMOIRE = "etat_bots.json"
SYMBOL = 'XRP/USDC'

def charger_donnees():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

kraken = get_kraken_connection()
memoire = charger_donnees()

if 'bots' not in st.session_state:
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
    st.session_state.profit_total = 0.0
    if memoire:
        st.session_state.bots.update(memoire.get("bots", {}))
        st.session_state.profit_total = memoire.get("profit_total", 0.0)

# --- 3. BARRE LATÉRALE (FIXE) ---
with st.sidebar:
    st.header("⚡ CMD CENTER")
    # Bouton manuel pour rafraîchir sans attendre
    if st.button("🔄 FORCE UPDATE", use_container_width=True):
        st.rerun()
    
    st.divider()
    mode_reel = st.toggle("LIVE TRADING", value=True)
    p_in_set = st.number_input("TARGET IN", value=1.4440, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4460, format="%.4f")
    budget_base = st.number_input("BASE USD", value=10.0)
    
    # Boutons Start/Stop
    for i in range(10):
        # ... (Garde ton code actuel de boutons ici) ...
        pass

# --- 4. AFFICHAGE ET LOGIQUE (FRAGMENTÉ) ---
# On rafraîchit uniquement cette partie toutes les 30 secondes
@st.fragment(run_every=30)
def zone_dynamique():
    try:
        # Données Marché
        ticker = kraken.fetch_ticker(SYMBOL)
        px = ticker['last']
        bal = kraken.fetch_balance()
        usdc = bal.get('total', {}).get('USDC', 0.0)

        st.write(f"### 🌐 TERMINAL STABLE - {SYMBOL}")
        k1, k2, k3 = st.columns(3)
        k1.metric("BANKROLL", f"{usdc:.2f} $")
        k2.metric("XRP PRICE", f"{px:.4f}")
        k3.metric("TOTAL NET", f"+{st.session_state.profit_total:.4f}")
        st.divider()

        # Monitoring Bots
        for i in range(10):
            name = f"Bot_{i+1}"
            bot = st.session_state.bots[name]
            if bot["status"] != "LIBRE" and bot["id"]:
                color = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                st.markdown(f'''
                <div class="bot-line">
                    <span style="color:#666">#{i+1:02d}</span>
                    <span style="color:{color}; font-weight:bold;">{bot["status"]}</span>
                    <span>{bot["p_achat"]} → {bot["p_vente"]}</span>
                    <span class="flash-box">{budget_base + bot['gain']:.2f}$</span>
                </div>''', unsafe_allow_html=True)
                
                # Check Order (Silencieux)
                order = kraken.fetch_order(bot['id'], SYMBOL)
                if order['status'] == 'closed':
                    # ... Logique de switch achat/vente (boule de neige) ...
                    # On sauvegarde mais on ne fait PAS de st.rerun() ici
                    st.toast(f"Bot {i+1} : Cycle complété !") 

    except Exception as e:
        st.caption(f"Sync... {str(e)[:25]}")

# Lancement
zone_dynamique()
