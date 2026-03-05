import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE "BLOOMBERG"
st.set_page_config(page_title="XRP Bloomberg DIAGNOSTIC", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    [data-testid="stMetric"] { background-color: #FFFFFF !important; border-radius: 4px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 20px !important; font-weight: 900 !important; }
    .bot-line { border-bottom: 1px solid #222222; padding: 8px 0px; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 2px 6px; border-radius: 2px; font-weight: 900; }
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
        st.session_state.bots = mem.get("bots")
        st.session_state.profit_total = mem.get("profit_total", 0.0)
    else:
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "oid": "NONE"} for i in range(100)}
        st.session_state.profit_total = 0.0
    st.session_state.bankroll = 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ CMD RÉEL")
    p_in_set = st.number_input("TARGET IN (ACHAT)", value=1.4000, format="%.4f")
    p_out_set = st.number_input("TARGET OUT (VENTE)", value=1.4500, format="%.4f")
    budget_val = st.number_input("BUDGET (USDC)", value=35.0)
    
    if st.button("🚨 RESET TOTAL"):
        st.session_state.bots = {f"B{i+1}": {"status": "LIBRE", "pa": 0.0, "pv": 0.0, "budget": 35.0, "gain": 0.0, "oid": "NONE"} for i in range(100)}
        st.session_state.profit_total = 0.0
        sauvegarder(st.session_state.bots, 0.0); st.rerun()

    for i in range(100):
        id_b = f"B{i+1}"
        c1, c2 = st.columns(2)
        if st.session_state.bots[id_b]["status"] == "LIBRE":
            if c1.button(f"GO {i+1}", key=f"g{i}"):
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in_set))
                pv_f = float(kraken.price_to_precision('XRP/USDC', p_out_set))
                st.session_state.bots[id_b].update({"status": "ACHAT", "pa": pa_f, "pv": pv_f, "budget": budget_val})
                sauvegarder(st.session_state.bots, st.session_state.profit_total); st.rerun()
        else:
            if c2.button(f"OFF {i+1}", key=f"o{i}"):
                st.session_state.bots[id_b].update({"status": "LIBRE", "oid": "NONE"}); st.rerun()

# --- BOUCLE PRINCIPALE AVEC DIAGNOSTIC ---
live = st.empty()
count = 0
while True:
    try:
        if not kraken.markets: kraken.load_markets()
        px = kraken.fetch_ticker('XRP/USDC')['last']
        if count % 5 == 0:
            st.session_state.bankroll = kraken.fetch_balance().get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET FEED : {px:.4f}")
            c1, c2 = st.columns(2)
            c1.metric("BANKROLL", f"{st.session_state.bankroll:.2f} USDC")
            c2.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            st.divider()
            
            actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
            
            for name in actifs:
                bot = st.session_state.bots[name]
                actuel_b = bot["budget"] + bot["gain"]
                vol = float(kraken.amount_to_precision('XRP/USDC', actuel_b / px))
                
                # --- DIAGNOSTIC VISUEL PAR BOT ---
                if bot["status"] == "ACHAT":
                    if px <= bot["pa"]:
                        st.warning(f"🚀 {name} : TENTATIVE D'ACHAT (Marché {px} <= Cible {bot['pa']})")
                        try:
                            # ON PLACE L'ORDRE LIMITE (post-only False pour forcer l'exécution si prix touché)
                            res = kraken.create_limit_buy_order('XRP/USDC', vol, bot["pa"], {'post-only': False})
                            st.session_state.bots[name].update({"status": "VENTE", "oid": res['id']})
                            sauvegarder(st.session_state.bots, st.session_state.profit_total)
                            st.success(f"🔥 KRAKEN ACCEPTE : {name} ID {res['id']}")
                        except Exception as e:
                            st.error(f"❌ KRAKEN REFUS {name} : {str(e)[:100]}")
                    else:
                        st.info(f"⏳ {name} : ATTENTE PRIX (Besoin de {bot['pa']} | Marché à {px})")

                elif bot["status"] == "VENTE":
                    if px >= bot["pv"]:
                        try:
                            res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["pv"], {'post-only': False})
                            g = (bot["pv"] - bot["pa"]) * vol
                            st.session_state.profit_total += g
                            st.session_state.bots[name].update({"status": "ACHAT", "gain": bot["gain"]+g, "oid": res['id']})
                            sauvegarder(st.session_state.bots, st.session_state.profit_total)
                            st.success(f"💰 VENTE RÉUSSIE : {name} (+{g:.2f})")
                        except Exception as e:
                            st.error(f"❌ KRAKEN REFUS {name} : {str(e)[:100]}")
                    else:
                        st.info(f"⏳ {name} : ATTENTE VENTE (Besoin de {bot['pv']} | Marché à {px})")

                # Affichage Ligne Bloomberg
                sc = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                st.markdown(f'<div class="bot-line"><span>{name}</span><span style="color:{sc};">{bot["status"]}</span><span>{bot["pa"]}->{bot["pv"]}</span><span class="flash-box">{actuel_b:.2f} USDC</span></div>', unsafe_allow_html=True)
                time.sleep(0.1)

    except Exception as e:
        if "nonce" in str(e).lower(): time.sleep(1)
        else: st.write(f"SYSTEM ERROR: {str(e)[:50]}")
    
    count += 1
    time.sleep(8)
