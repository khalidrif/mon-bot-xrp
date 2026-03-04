import streamlit as st
import pandas as pd
import ccxt
import time
import datetime
import json
import os
from config import get_kraken_connection

# 1. STYLE "TARGET VISION"
st.set_page_config(page_title="XRP Gold Real Money", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; }
    [data-testid="stMetric"] { background-color: #1A1A00; border: 1px solid #FFD700; padding: 10px; border-radius: 10px; }
    .bot-number { color: #00FFFF !important; font-size: 18px !important; font-weight: bold; border-bottom: 1px solid #00FFFF; margin-bottom: 5px; }
    .target-box { font-size: 11px; color: #888888; margin-top: 5px; line-height: 1.2; }
    .target-buy { color: #FFA500; font-weight: bold; }
    .target-sell { color: #00FF88; font-weight: bold; }
    .highlight-val { background-color: #FFFF00; color: #000000; padding: 1px 5px; border-radius: 3px; font-weight: bold; font-family: monospace; font-size: 12px; }
    [data-testid="stMetricValue"] { color: #FFFF00 !important; font-family: 'Courier New', monospace; font-size: 24px !important; }
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

memoire = charger_donnees()
if 'bots' not in st.session_state:
    if memoire:
        st.session_state.bots = memoire["bots"]
        st.session_state.profit_total = memoire["profit_total"]
    else:
        st.session_state.bots = {f"Bot_{i+1}": {"id": None, "status": "LIBRE", "p_achat": 0.0, "p_vente": 0.0, "cycles": 0, "gain": 0.0} for i in range(10)}
        st.session_state.profit_total = 0.0

kraken = get_kraken_connection()

# 3. SIDEBAR
with st.sidebar:
    st.header("🟡 Gold Real Control")
    # --- CHANGEMENT ICI : value=True pour laisser activé ---
    mode_reel = st.toggle("💰 ARGENT RÉEL", value=True) 
    
    st.divider()
    p_achat_in = st.number_input("Achat ($)", value=1.3560, format="%.4f")
    p_vente_in = st.number_input("Vente ($)", value=1.3650, format="%.4f")
    budget_in = st.number_input("Budget ($)", value=10.0)
    st.divider()
    for i in range(10):
        name = f"Bot_{i+1}"
        c_l, c_s = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if c_l.button(f"GO {i+1}", key=f"l_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    kraken.load_markets()
                    qty = (budget_in + st.session_state.bots[name]["gain"]) / p_achat_in
                    pa, pv = float(kraken.price_to_precision('XRP/USDC', p_achat_in)), float(kraken.price_to_precision('XRP/USDC', p_vente_in))
                    # L'ordre est REEL si mode_reel est coché (il l'est par défaut maintenant)
                    res = kraken.create_order('XRP/USDC', 'limit', 'buy', float(kraken.amount_to_precision('XRP/USDC', qty)), pa, {'validate': not mode_reel})
                    st.session_state.bots[name].update({"id": res['id'], "status": "ACHAT", "p_achat": pa, "p_vente": pv})
                    sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                    st.rerun()
                except Exception as e: st.error(e)
        else:
            if c_s.button(f"STOP {i+1}", key=f"stop_{i}"):
                try:
                    kraken.options['nonce'] = lambda: int(time.time() * 1000)
                    kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                st.rerun()

# 4. ZONE LIVE
st.title("🛰️ Quantum Gold : Mode Réel")
zone_live = st.empty()

while True:
    try:
        kraken.options['nonce'] = lambda: int(time.time() * 1000)
        # --- CORRECTIF PRIX (Extraction sécurisée) ---
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        p_ask = float(ob['asks'][0][0])
        p_bid = float(ob['bids'][0][0])
        prix_reel = (p_ask + p_bid) / 2
        
        balance = kraken.fetch_balance()
        usdc = balance.get('free', {}).get('USDC', balance.get('free', {}).get('ZUSD', 0))

        with zone_live.container():
            c1, c2, c3 = st.columns(3)
            c1.metric("SOLDE", f"{usdc:,.2f} $")
            c2.metric("PRIX XRP", f"{prix_reel:.4f} $")
            c3.metric("GAINS", f"+{st.session_state.profit_total:.4f} $")
            st.divider()
            
            r1 = st.columns(5)
            r2 = st.columns(5)
            all_cols = r1 + r2

            for i in range(10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                with all_cols[i]:
                    st.markdown(f'<p class="bot-number">BOT {i+1}</p>', unsafe_allow_html=True)
                    val_live = budget_in + bot['gain']
                    
                    if bot["status"] == "ACHAT":
                        st.warning(f"📥 ACHAT @{bot['p_achat']}")
                        info = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        if info['status'] == 'closed':
                            res_v = kraken.create_order('XRP/USDC', 'limit', 'sell', info['filled'], bot['p_vente'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res_v['id'], "status": "VENTE"})
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.rerun()
                    elif bot["status"] == "VENTE":
                        st.success(f"📤 VENTE @{bot['p_vente']}")
                        val_live = (budget_in + bot['gain']) / bot['p_achat'] * prix_reel
                        info_v = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        if info_v['status'] == 'closed':
                            gain = (bot['p_vente'] - bot['p_achat']) * info_v['filled']
                            st.session_state.profit_total += gain
                            st.session_state.bots[name]["gain"] += gain
                            st.session_state.bots[name]["cycles"] += 1
                            q = float(kraken.amount_to_precision('XRP/USDC', (budget_in + st.session_state.bots[name]["gain"]) / bot['p_achat']))
                            res_n = kraken.create_order('XRP/USDC', 'limit', 'buy', q, bot['p_achat'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res_n['id'], "status": "ACHAT"})
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.balloons()
                            st.rerun()
                    else: st.caption("Repos")

                    if bot["status"] != "LIBRE":
                        st.markdown(f'''
                        <div class="target-box">
                            In: <span class="target-buy">{bot['p_achat']}</span> | 
                            Out: <span class="target-sell">{bot['p_vente']}</span>
                        </div>
                        ''', unsafe_allow_html=True)

                    st.write(f"🔄 {bot['cycles']} | 💰 {bot['gain']:.4f}$")
                    st.markdown(f'Valeur: <span class="highlight-val">{val_live:.2f} $</span>', unsafe_allow_html=True)

    except Exception as e:
        if "nonce" in str(e).lower(): time.sleep(1); continue
        st.write(f"Flux... {e}")

    time.sleep(20)
