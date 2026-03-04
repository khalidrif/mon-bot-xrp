import streamlit as st
import pandas as pd
import ccxt
import time
import datetime
import json
import os
from config import get_kraken_connection

# 1. STYLE ZEN GOLD (Barre Jaune sur Fond Noir)
st.set_page_config(page_title="XRP Precision Bot", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stMetric"] { background-color: #1A1C23; border: 1px solid #30363D; border-radius: 8px; padding: 10px; }
    
    /* LA BARRE : Fond Noir, Remplissage Jaune Fluo */
    .stProgress > div > div > div > div { background-color: #FFFF00 !important; }
    .stProgress > div > div { background-color: #000000 !important; height: 12px !important; border-radius: 6px; border: 1px solid #30363D; }
    
    .small-price { font-size: 11px; color: #8B949E; }
    .status-bold { font-size: 13px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. MÉMOIRE
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

# Initialisation
memoire = charger_donnees()
if 'bots' not in st.session_state:
    st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
    st.session_state.profit_total = 0.0
    if memoire:
        st.session_state.bots.update(memoire["bots"])
        st.session_state.profit_total = memoire["profit_total"]

# --- SIDEBAR (Réglages 1.12 / 1.44) ---
with st.sidebar:
    st.header("🎯 Cibles")
    mode_reel = st.toggle("Argent Réel", value=True)
    p_in = st.number_input("Achat (ex: 1.12)", value=1.1200, format="%.4f")
    p_out = st.number_input("Vente (ex: 1.44)", value=1.4400, format="%.4f")
    budget = st.number_input("Budget ($)", value=10.0)
    
    st.divider()
    for i in range(10):
        name = f"Bot_{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c1.button(f"Lancer {i+1}", key=f"go_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    qty = (budget + st.session_state.bots[name]["gain"]) / p_in
                    pa, pv = float(kraken.price_to_precision('XRP/USDC', p_in)), float(kraken.price_to_precision('XRP/USDC', p_out))
                    res = kraken.create_order('XRP/USDC', 'limit', 'buy', float(kraken.amount_to_precision('XRP/USDC', qty)), pa, {'validate': not mode_reel})
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(f"Erreur: {e}")
        else:
            if c2.button(f"Stop {i+1}", key=f"off_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# --- MAIN ---
st.title("🛰️ XRP Precision Terminal")
live = st.empty()

while True:
    try:
        kraken.options['nonce'] = lambda: int(time.time() * 1000)
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        px = (float(ob['asks']) + float(ob['bids'])) / 2
        bal = kraken.fetch_balance()
        usdc = bal.get('free', {}).get('USDC', bal.get('free', {}).get('ZUSD', 0))

        with live.container():
            m1, m2, m3 = st.columns(3)
            m1.metric("SOLDE", f"{usdc:,.2f} $")
            m2.metric("PRIX XRP", f"{px:.4f} $")
            m3.metric("GAINS", f"+{st.session_state.profit_total:.4f} $")
            
            st.divider()
            cols = st.columns(5)
            cols2 = st.columns(5)
            all_c = cols + cols2

            for i in range(10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                with all_c[i]:
                    st.write(f"**Bot {i+1}**")
                    if bot["status"] != "LIBRE":
                        # CALCUL FOURCHETTE (Position entre 1.12 et 1.44)
                        low, high = bot['p_achat'], bot['p_vente']
                        prog = (px - low) / (high - low) if (high - low) != 0 else 0
                        st.progress(min(max(prog, 0.0), 1.0))
                        
                        if bot["status"] == "ACHAT":
                            st.markdown(f'<span class="status-bold" style="color:#FFA500;">📥 ACHAT</span> <span class="small-price">@{bot["p_achat"]}</span>', unsafe_allow_html=True)
                            info = kraken.fetch_order(bot['id'], 'XRP/USDC')
                            if info['status'] == 'closed':
                                res_v = kraken.create_order('XRP/USDC', 'limit', 'sell', info['filled'], bot['p_vente'], {'validate': not mode_reel})
                                st.session_state.bots[name].update({"id": res_v['id'], "status": "VENTE"})
                                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                                st.rerun()
                        elif bot["status"] == "VENTE":
                            st.markdown(f'<span class="status-bold" style="color:#00FF88;">📤 VENTE</span> <span class="small-price">@{bot["p_vente"]}</span>', unsafe_allow_html=True)
                            info_v = kraken.fetch_order(bot['id'], 'XRP/USDC')
                            if info_v['status'] == 'closed':
                                g = (bot['p_vente'] - bot['p_achat']) * info_v['filled']
                                st.session_state.profit_total += g
                                st.session_state.bots[name]["gain"] += g
                                st.session_state.bots[name]["cycles"] += 1
                                # BOULE DE NEIGE
                                q = float(kraken.amount_to_precision('XRP/USDC', (budget + st.session_state.bots[name]["gain"]) / bot['p_achat']))
                                res_n = kraken.create_order('XRP/USDC', 'limit', 'buy', q, bot['p_achat'], {'validate': not mode_reel})
                                st.session_state.bots[name].update({"id": res_n['id'], "status": "ACHAT"})
                                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                                st.rerun()
                    else:
                        st.write("---")
                    st.caption(f"Cycles: {bot['cycles']} | +{bot['gain']:.2f}$")

    except Exception as e:
        if "nonce" in str(e).lower(): time.sleep(1); continue
        st.write(f"Sync... {e}")
    time.sleep(20)
