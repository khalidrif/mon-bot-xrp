import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE "LIGHT TERMINAL" (PLUS FLUIDE)
st.set_page_config(page_title="XRP Light Bot", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .price-box { 
        text-align: center; 
        padding: 20px; 
        background: white; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 25px;
        border-top: 5px solid #0070FF;
    }
    .price-val { font-size: 55px !important; font-weight: 900; color: #111; }
    .bot-line { 
        background: white;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-v { color: #28a745; font-weight: 800; }
    .status-a { color: #fd7e14; font-weight: 800; }
    .cycle-badge { background: #007bff; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .money { font-weight: 900; color: #222; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION ET MÉMOIRE
kraken = get_kraken_connection()
FILE_MEMOIRE = "etat_bots.json"

def sauvegarder(bots, total):
    with open(FILE_MEMOIRE, "w") as f: json.dump({"bots": bots, "profit_total": total}, f)

def charger():
    if os.path.exists(FILE_MEMOIRE):
        try:
            with open(FILE_MEMOIRE, "r") as f: return json.load(f)
        except: return None
    return None

if 'bots' not in st.session_state:
    mem = charger()
    if mem:
        st.session_state.bots, st.session_state.profit_total = mem.get("bots"), mem.get("profit_total", 0.0)
    else:
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.session_state.profit_total = 0.0
    st.session_state.bankroll = 0.0

# --- SIDEBAR (LIMITÉE À 20 BOTS POUR LA FLUIDITÉ) ---
with st.sidebar:
    st.title("⚙️ CONFIG")
    p_in = st.number_input("TARGET ACHAT", value=1.4000, format="%.4f")
    p_out = st.number_input("TARGET VENTE", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET UNITAIRE", value=35.0)
    
    st.divider()
    if st.button("🚨 RESET TOUT"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
        st.session_state.profit_total = 0.0
        sauvegarder(st.session_state.bots, 0.0); st.rerun()

    for i in range(20):
        id_b = f"B{i+1}"
        col1, col2 = st.columns([3, 1])
        if st.session_state.bots[id_b]["status"] == "LIBRE":
            if col1.button(f"LANCER {i+1}", key=f"g{i}"):
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                pv_f = float(kraken.price_to_precision('XRP/USDC', p_out))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                try:
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                    st.session_state.bots[id_b].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "budget": b_val, "oid": res['id']})
                    sauvegarder(st.session_state.bots, st.session_state.profit_total); st.rerun()
                except Exception as e: st.error("Kraken Error")
        else:
            if col2.button("X", key=f"o{i}"):
                st.session_state.bots[id_b]["status"] = "LIBRE"; st.rerun()

# --- MAIN ---
live = st.empty()
count = 0
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        if count % 5 == 0:
            st.session_state.bankroll = kraken.fetch_balance().get('USDC', {}).get('free', 0.0)
        
        with live.container():
            # PRIX CENTRAL
            st.markdown(f'<div class="price-box"><div style="color:#666; font-size:14px;">XRP/USDC MARKET</div><div class="price-val">{px:.4f}</div></div>', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("SOLDE", f"{st.session_state.bankroll:.2f} $")
            c2.metric("GAINS", f"+{st.session_state.profit_total:.4f} $")
            c3.metric("ACTIFS", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            
            st.divider()
            
            # AFFICHAGE UNIQUEMENT DES BOTS ACTIFS
            actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
            if not actifs:
                st.info("Aucun bot actif. Lancez-en un depuis la barre latérale.")
            
            for name in actifs:
                bot = st.session_state.bots[name]
                st_lab = "VENTE" if bot["status"] == "VENTE" else "ACHAT"
                st_col = "status-v" if bot["status"] == "VENTE" else "status-a"
                val_now = bot["budget"] + bot["gain"]
                
                st.markdown(f'''
                    <div class="bot-line">
                        <b>{name}</b>
                        <span class="{st_col}">{st_lab}</span>
                        <span>{bot["pa"]} → {bot["pv"]}</span>
                        <span class="cycle-badge">{bot.get("cycles", 0)} CYC</span>
                        <span class="money">{val_now:.2f} USDC</span>
                    </div>
                ''', unsafe_allow_html=True)
    except:
        pass
    count += 1
    time.sleep(15)
