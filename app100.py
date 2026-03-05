import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE "BLOOMBERG HIGH-CONTRAST"
st.set_page_config(page_title="XRP Bloomberg FORCE LIVE", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    [data-testid="stMetric"] { background-color: #FFFFFF !important; border-radius: 4px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 20px !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; font-size: 12px !important; font-weight: bold !important; }
    .bot-line { border-bottom: 1px solid #222222; padding: 8px 0px; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
    .p-in { color: #00FF00; font-weight: bold; }
    .p-out { color: #FF0000; font-weight: bold; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 2px 6px; border-radius: 2px; font-weight: 900; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION ET MÉMOIRE
kraken = get_kraken_connection()
FILE_MEMOIRE = "etat_bots.json"

def sauvegarder_donnees(bots, profit_total):
    with open(FILE_MEMOIRE, "w") as f: json.dump({"bots": bots, "profit_total": profit_total}, f)

def charger_donnees():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

if 'bots' not in st.session_state:
    memoire = charger_donnees()
    if memoire:
        st.session_state.bots = memoire.get("bots")
        st.session_state.profit_total = memoire.get("profit_total", 0.0)
    else:
        st.session_state.bots = {f"Bot_{i+1}": {"status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(100)}
        st.session_state.profit_total = 0.0
    st.session_state.bankroll = 0.0

# --- SIDEBAR CMD ---
with st.sidebar:
    st.header("⚡ CMD")
    p_in_set = st.number_input("TARGET IN", value=1.4440, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4460, format="%.4f")
    budget_base = st.number_input("BASE USDC", value=10.0)
    
    c_a, c_b = st.columns(2)
    if c_a.button("🚨 RESET"):
        st.session_state.profit_total = 0.0
        for b in st.session_state.bots: st.session_state.bots[b].update({"gain": 0.0, "cycles": 0})
        sauvegarder_donnees(st.session_state.bots, 0.0); st.rerun()
    if c_b.button("🛑 STOP ALL"):
        for b in st.session_state.bots: st.session_state.bots[b].update({"status": "LIBRE"})
        sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total); st.rerun()

    for i in range(100):
        name = f"Bot_{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"g{i}"):
                if not kraken.markets: kraken.load_markets()
                pa = float(kraken.price_to_precision('XRP/USDC', p_in_set))
                pv = float(kraken.price_to_precision('XRP/USDC', p_out_set))
                st.session_state.bots[name].update({"status": "ACHAT", "p_achat": pa, "p_vente": pv})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total); st.rerun()
        else:
            if c2.button(f"OFF {i+1}", key=f"o{i}"):
                st.session_state.bots[name].update({"status": "LIBRE"}); st.rerun()

# --- BOUCLE PRINCIPALE (ULTRA-STABLE) ---
live = st.empty()
count = 0

while True:
    try:
        if not kraken.markets: kraken.load_markets()
        
        # 1. PRIX (Essentiel)
        ticker = kraken.fetch_ticker('XRP/USDC')
        px = ticker['last']
        
        # 2. BALANCE (Toutes les 10 boucles seulement pour économiser l'API)
        if count % 10 == 0:
            bal = kraken.fetch_balance()
            st.session_state.bankroll = bal.get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET FEED - XRP/USDC (LIVE)")
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{st.session_state.bankroll:.2f} USDC")
            c2.metric("XRP PRICE", f"{px:.4f}")
            c3.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            st.divider()
            
            # FILTRE : Uniquement les bots actifs
            actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
            
            # ROTATION : On traite par groupes de 5 pour ne pas saturer Kraken
            start_idx = (count % max(1, len(actifs) // 5 + 1)) * 5
            selection = actifs[start_idx : start_idx + 5]
            
            for name in actifs: # On affiche tout, mais on ne trade que la 'selection'
                bot = st.session_state.bots[name]
                val_snow = budget_base + bot['gain']
                vol = float(kraken.amount_to_precision('XRP/USDC', val_snow / px))
                
                if name in selection:
                    # LOGIQUE ACHAT
                    if bot["status"] == "ACHAT" and px <= bot["p_achat"]:
                        kraken.create_limit_buy_order('XRP/USDC', vol, bot["p_achat"])
                        st.session_state.bots[name]["status"] = "VENTE"
                        sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                        st.toast(f"✅ BUY {name}")
                    
                    # LOGIQUE VENTE
                    elif bot["status"] == "VENTE" and px >= bot["p_vente"]:
                        kraken.create_limit_sell_order('XRP/USDC', vol, bot["p_vente"])
                        g = (bot['p_vente'] - bot['p_achat']) * vol
                        st.session_state.profit_total += g
                        st.session_state.bots[name].update({"gain": bot["gain"]+g, "cycles": bot["cycles"]+1, "status": "ACHAT"})
                        sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                        st.toast(f"💰 PROFIT {name} (+{g:.2f})")
                    
                    time.sleep(1.0) # Pause de sécurité entre bots sélectionnés

                # AFFICHAGE TOUJOURS ACTIF
                sc = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                st.markdown(f'<div class="bot-line"><span>{name}</span><span style="color:{sc};">{bot["status"]}</span><span>{bot["p_achat"]}->{bot["p_vente"]}</span><span class="flash-box">{val_snow:.2f} USDC</span></div>', unsafe_allow_html=True)
            
        count += 1
        sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)

    except Exception as e:
        if "Rate limit" in str(e):
            st.warning("⚠️ Limite API Kraken atteinte. Pause de 60s...")
            time.sleep(60)
        elif "nonce" in str(e).lower(): time.sleep(2)
        else: st.write(f"SYSTEM: {str(e)[:40]}")
    
    time.sleep(30) # Pause globale entre les cycles de rotation
