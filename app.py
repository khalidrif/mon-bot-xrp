import streamlit as st
import pandas as pd
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE "CRISTAL MINIMALISTE" (Zéro Jaune, Zéro Gras)
st.set_page_config(page_title="XRP Cristal", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; font-family: sans-serif; }
    
    /* Metrics épurées : Texte blanc, pas de gras, pas de fond */
    [data-testid="stMetric"] { 
        background-color: transparent !important; 
        border: none !important;
    }
    [data-testid="stMetricValue"] { 
        color: #FFFFFF !important; 
        font-size: 26px !important; 
        font-weight: 300 !important; /* Texte très fin */
    }
    [data-testid="stMetricLabel"] { 
        color: #888888 !important; 
        font-size: 12px !important; 
    }

    .bot-line {
        border-bottom: 1px solid #1A1A1A;
        padding: 5px 0px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 13px;
        color: #BBBBBB;
    }
    
    /* Couleurs de statut fines */
    .p-in { color: #44CC44; } /* Vert doux */
    .p-out { color: #CC4444; } /* Rouge doux */
    
    /* Boîtes de données grises et fines */
    .data-box {
        border: 1px solid #333333;
        color: #FFFFFF;
        padding: 1px 4px;
        border-radius: 2px;
        font-size: 12px;
    }
    .bot-id { color: #444444; }
    </style>
    """, unsafe_allow_html=True)

# 2. MÉMOIRE ET CONFIG
FILE_MEMOIRE = "etat_bots.json"
def sauvegarder_donnees(bots, profit_total):
    with open(FILE_MEMOIRE, "w") as f: json.dump({"bots": bots, "profit_total": profit_total}, f)

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
        st.session_state.bots.update(memoire["bots"])
        st.session_state.profit_total = memoire.get("profit_total", 0.0)

# --- SIDEBAR ---
with st.sidebar:
    st.caption("PARAMÈTRES")
    mode_reel = st.toggle("TRADING RÉEL", value=True)
    p_in_set = st.number_input("CIBLE ACHAT", value=1.4440, format="%.4f")
    p_out_set = st.number_input("CIBLE VENTE", value=1.4460, format="%.4f")
    budget_base = st.number_input("BUDGET USD", value=10.0)
    st.divider()
    for i in range(10):
        name = f"Bot_{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c1.button(f"RUN {i+1}", key=f"l_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    budget_actuel = budget_base + st.session_state.bots[name]["gain"]
                    qty = budget_actuel / p_in_set
                    pa, pv = float(kraken.price_to_precision('XRP/USDC', p_in_set)), float(kraken.price_to_precision('XRP/USDC', p_out_set))
                    res = kraken.create_order('XRP/USDC', 'limit', 'buy', float(kraken.amount_to_precision('XRP/USDC', qty)), pa, {'validate': not mode_reel})
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(e)
        else:
            if c2.button(f"STOP {i+1}", key=f"off_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# --- MAIN ---
live = st.empty()

while True:
    try:
        kraken.options['nonce'] = lambda: int(time.time() * 1000)
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        p_ask = float(ob['asks'][0][0]) if ob['asks'] else 0.0
        p_bid = float(ob['bids'][0][0]) if ob['bids'] else 0.0
        px = (p_ask + p_bid) / 2
        
        bal = kraken.fetch_balance()
        usdc = bal.get('free', {}).get('USDC', bal.get('free', {}).get('ZUSD', 0))

        with live.container():
            st.caption("FLUX TEMPS RÉEL XRP/USDC")
            c1, c2, c3 = st.columns(3)
            c1.metric("SOLDE DISPONIBLE", f"{usdc:.2f}$")
            c2.metric("PRIX DU MARCHÉ", f"{px:.4f}")
            c3.metric("GAINS NETS", f"+{st.session_state.profit_total:.4f}")
            
            st.divider()
            
            for i in range(10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                if bot["status"] != "LIBRE":
                    val_snow = budget_base + bot['gain']
                    st.markdown(f'''
                    <div class="bot-line">
                        <span class="bot-id">#{i+1:02d}</span>
                        <span>{bot["status"]}</span>
                        <span><span class="p-in">{bot["p_achat"]}</span> → <span class="p-out">{bot["p_vente"]}</span></span>
                        <span class="data-box">{val_snow:.2f}$</span>
                        <span class="data-box">{bot["cycles"]} cycles</span>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    info = kraken.fetch_order(bot['id'], 'XRP/USDC')
                    if info['status'] == 'closed':
                        if bot["status"] == "ACHAT":
                            res = kraken.create_order('XRP/USDC', 'limit', 'sell', info['filled'], bot['p_vente'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res['id'], "status": "VENTE"})
                        else:
                            g = (bot['p_vente'] - bot['p_achat']) * info['filled']
                            st.session_state.profit_total += g
                            st.session_state.bots[name]["gain"] += g
                            st.session_state.bots[name]["cycles"] += 1
                            new_budget = budget_base + st.session_state.bots[name]["gain"]
                            q = float(kraken.amount_to_precision('XRP/USDC', new_budget / bot['p_achat']))
                            res = kraken.create_order('XRP/USDC', 'limit', 'buy', q, bot['p_achat'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT"})
                        sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                        st.rerun()

    except Exception as e:
        if "nonce" in str(e).lower(): time.sleep(1); continue
        st.write(f"SYSTÈME: {str(e)[:20]}")
    time.sleep(20)
