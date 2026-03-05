import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. LOOK PRO MAIS LÉGER
st.set_page_config(page_title="XRP Light Terminal", layout="wide")
st.markdown("""
    <style>
    .price-box { text-align: center; padding: 15px; background: #f0f2f6; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #0070FF; }
    .price-val { font-size: 40px; font-weight: 900; color: #111; }
    .bot-line { border-bottom: 1px solid #eee; padding: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
    .status-v { color: #28a745; font-weight: bold; }
    .status-a { color: #fd7e14; font-weight: bold; }
    .cycle-badge { background: #007bff; color: white; padding: 1px 6px; border-radius: 3px; font-size: 11px; }
    .money { font-weight: bold; color: #222; }
    </style>
    """, unsafe_allow_html=True)

# 2. MÉMOIRE
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
    st.session_state.bots = mem.get("bots") if mem else {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "oid": "NONE", "cycles": 0} for i in range(100)}
    st.session_state.profit_total = mem.get("profit_total", 0.0) if mem else 0.0

# --- SIDEBAR (LÉGÈRE) ---
with st.sidebar:
    st.title("⚙️ SETUP")
    p_in = st.number_input("ACHAT", value=1.4000, format="%.4f")
    p_out = st.number_input("VENTE", value=1.4500, format="%.4f")
    b_val = st.number_input("BUDGET", value=35.0)
    
    st.divider()
    # On n'affiche que les 10 premiers GO pour ne pas surcharger la sidebar
    # Tu peux changer le range(10) par (100) si tu as besoin de tous les voir
    for i in range(20):
        id_b = f"B{i+1}"
        col1, col2 = st.columns([3, 1])
        if st.session_state.bots[id_b]["status"] == "LIBRE":
            if col1.button(f"🚀 LANCER {i+1}", key=f"g{i}", use_container_width=True):
                if not kraken.markets: kraken.load_markets()
                pa_f, pv_f = float(kraken.price_to_precision('XRP/USDC', p_in)), float(kraken.price_to_precision('XRP/USDC', p_out))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                try:
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                    st.session_state.bots[id_b].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "budget": b_val, "oid": res['id']})
                    sauvegarder(st.session_state.bots, st.session_state.profit_total); st.rerun()
                except Exception as e: st.error("Erreur API")
        else:
            if col2.button("✖", key=f"o{i}"):
                st.session_state.bots[id_b]["status"] = "LIBRE"; st.rerun()

# --- MAIN ---
live = st.empty()
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        with live.container():
            st.markdown(f'<div class="price-box"><div class="price-val">{px:.4f}</div><div style="color:#666">XRP/USDC</div></div>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            c1.metric("GAINS CUMULÉS", f"+{st.session_state.profit_total:.4f} USDC")
            c2.metric("BOTS ACTIFS", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            
            st.write("---")
            # ON N'AFFICHE QUE LES BOTS QUI TRAVAILLENT
            for name, bot in st.session_state.bots.items():
                if bot["status"] != "LIBRE":
                    label = "VENTE" if bot["status"] == "VENTE" else "ACHAT"
                    color = "status-v" if bot["status"] == "VENTE" else "status-a"
                    val = bot["budget"] + bot["gain"]
                    
                    st.markdown(f'''
                        <div class="bot-line">
                            <b>{name}</b>
                            <span class="{color}">{label}</span>
                            <span>{bot["pa"]} → {bot["pv"]}</span>
                            <span class="cycle-badge">{bot.get("cycles", 0)} CYC</span>
                            <span class="money">{val:.2f} $</span>
                        </div>''', unsafe_allow_html=True)
    except: pass
    time.sleep(15)
