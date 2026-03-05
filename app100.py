import streamlit as st
import sys
import json
import os

# --- PATCH DE SÉCURITÉ CCXT ---
try:
    import ccxt
except ImportError:
    st.error("Installation des composants en cours...")
    st.stop()

from streamlit_autorefresh import st_autorefresh
from config import get_kraken_connection

# 1. CONFIGURATION & REFRESH AUTO (15s)
st.set_page_config(page_title="XRP Terminal Pro", layout="wide")
st_autorefresh(interval=15000, key="datarefresh") 

# 2. GESTION DE LA MÉMOIRE (POUR NE RIEN PERDRE)
FILE_MEMOIRE = "etat_bots.json"

def sauvegarder_donnees(bots, total):
    with open(FILE_MEMOIRE, "w") as f:
        json.dump({"bots": bots, "profit_total": total}, f)

def charger_donnees():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f:
                return json.load(f)
        except: return None
    return None

# 3. INITIALISATION (CHARGEMENT AUTO AU DÉMARRAGE)
if 'bots' not in st.session_state:
    memoire = charger_donnees()
    if memoire:
        st.session_state.bots = memoire.get("bots")
        st.session_state.profit_total = memoire.get("profit_total", 0.0)
    else:
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 25.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.session_state.profit_total = 0.0

# --- STYLE CSS (CLAIRE) ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F2F6 !important; }
    .status-dot { height: 10px; width: 10px; background-color: #00FF00; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #00FF00; animation: blinker 1.5s linear infinite; margin-right: 10px; }
    @keyframes blinker { 50% { opacity: 0; } }
    .bot-line { border-bottom: 1px solid #E6E9EF; padding: 12px 10px; display: flex; justify-content: space-between; align-items: center; background-color: #FFFFFF; margin-bottom: 3px; border-radius: 5px; font-size: 13px; }
    .status-v { color: #28a745; font-weight: bold; width: 60px; }
    .status-a { color: #fd7e14; font-weight: bold; width: 60px; }
    .flash-box { background-color: #FFC107; color: black; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .badge-cycle { background-color: #EAECEE; color: #1B2631; padding: 1px 10px; border-radius: 3px; font-size: 11px; font-weight: 900; border: 1px solid #D5D8DC; }
    </style>
    """, unsafe_allow_html=True)

# 4. CONNEXION KRAKEN + FIX MARKETS
kraken = get_kraken_connection()

# --- SIDEBAR CMD ---
with st.sidebar:
    st.header("⚙️ CONFIGURATION")
    p_in = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET (USDC)", value=25.0)
    
    bot_sel = st.selectbox("SÉLECTIONNER BOT", [f"B{i+1}" for i in range(100)])
    
    if st.button(f"🚀 GO {bot_sel}", use_container_width=True):
        if kraken:
            try:
                # --- FIX : CHARGEMENT DES MARCHES AVANT ORDRE ---
                if not kraken.markets:
                    kraken.load_markets()
                
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                
                # Placement de l'ordre réel
                res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                
                # Enregistrement
                st.session_state.bots[bot_sel].update({"status": "ACHAT", "pa": pa_f, "pv": p_out, "oid": res['id'], "budget": b_val})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.success(f"{bot_sel} LANCÉ !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur Kraken : {str(e)[:100]}")

    if st.button("🚨 STOP TOUS LES BOTS", use_container_width=True):
        for b in st.session_state.bots:
            st.session_state.bots[b].update({"status": "LIBRE", "oid": "NONE"})
        sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
        st.rerun()

# --- MAIN DISPLAY ---
try:
    # On s'assure que les marchés sont chargés pour le ticker aussi
    if not kraken.markets:
        kraken.load_markets()
        
    ticker = kraken.fetch_ticker('XRP/USDC')
    px = ticker['last']
    bal = kraken.fetch_balance()
    cash = bal.get('USDC', {}).get('free', 0.0)

    st.markdown(f'<h3><span class="status-dot"></span>TERMINAL XRP LIVE</h3>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX XRP", f"{px:.4f} $")
    c2.metric("GAIN TOTAL", f"+{st.session_state.profit_total:.4f} $")
    c3.metric("CASH DISPO", f"{cash:.2f} $")
    st.divider()

    # --- FILTRAGE : ON N'AFFICHE QUE LES BOTS ACTIFS ---
    actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
    if not actifs:
        st.info("Aucun bot actif. Utilisez la barre latérale pour démarrer.")
    else:
        for name in actifs:
            bot = st.session_state.bots[name]
            st.markdown(f'''
                <div class="bot-line">
                    <b style="color:#2C3E50;">{name}</b>
                    <span class="{"status-v" if bot["status"] == "VENTE" else "status-a"}">{bot["status"]}</span>
                    <span>{bot["pa"]:.4f} → {bot["pv"]:.4f}</span>
                    <span class="badge-cycle">{bot.get("cycles", 0)} CYCLES</span>
                    <span class="flash-box">{bot["budget"] + bot["gain"]:.2f} $</span>
                </div>''', unsafe_allow_html=True)
except Exception as e:
    st.info("Connexion Kraken en cours...")
