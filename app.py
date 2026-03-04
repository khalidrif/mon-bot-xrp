import streamlit as st
import pandas as pd
import ccxt
import time
import datetime
from config import get_kraken_connection

# 1. STYLE "GOLD TRADER"
st.set_page_config(page_title="XRP Gold Loop", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    [data-testid="stMetric"] {
        background-color: #1A1A00; 
        border: 2px solid #FFD700; 
        padding: 20px;
        border-radius: 15px;
    }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; }
    [data-testid="stMetricValue"] { 
        color: #FFFF00 !important; 
        font-family: 'Courier New', monospace; 
        font-size: 30px !important;
        text-shadow: 0px 0px 5px #FFFF00;
    }
    </style>
    """, unsafe_allow_html=True)

# Connexion
kraken = get_kraken_connection()
kraken.options['nonce'] = lambda: int(time.time() * 1000)

# --- MÉMOIRE DES BOTS ---
if 'bots' not in st.session_state:
    st.session_state.bots = {
        f"Bot_{i+1}": {
            "id": None, "status": "LIBRE", 
            "p_achat": 0.0, "p_vente": 0.0,
            "cycles": 0, "gain": 0.0
        } for i in range(10)
    }

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🟡 Gold Pilot")
    mode_reel = st.toggle("💰 ARGENT RÉEL", value=False)
    p_achat_input = st.number_input("Prix d'Achat ($)", value=1.3560, format="%.4f")
    p_vente_input = st.number_input("Prix de Vente ($)", value=1.3650, format="%.4f")
    budget_input = st.number_input("Budget ($)", value=10.0)

    st.divider()
    st.write("Lancer / Arrêter :")
    # On crée 10 lignes simples pour éviter les erreurs de colonnes imbriquées
    for i in range(10):
        name = f"Bot_{i+1}"
        col_l, col_s = st.columns(2)
        if st.session_state.bots[name]["status"] == "LIBRE":
            if col_l.button(f"LANCER {i+1}", key=f"l_{i}"):
                try:
                    kraken.load_markets()
                    qty = budget_input / p_achat_input
                    pa = float(kraken.price_to_precision('XRP/USDC', p_achat_input))
                    pv = float(kraken.price_to_precision('XRP/USDC', p_vente_input))
                    q = float(kraken.amount_to_precision('XRP/USDC', qty))
                    res = kraken.create_order('XRP/USDC', 'limit', 'buy', q, pa, {'validate': not mode_reel})
                    st.session_state.bots[name].update({"id": res['id'], "status": "ATTENTE_ACHAT", "p_achat": pa, "p_vente": pv})
                    st.rerun()
                except Exception as e: st.error(f"Erreur: {e}")
        else:
            if col_s.button(f"STOP {i+1}", key=f"stop_{i}"):
                try: kraken.cancel_order(st.session_state.bots[name]["id"])
                except: pass
                st.session_state.bots[name].update({"id": None, "status": "LIBRE"})
                st.rerun()

st.title("🛰️ XRP Gold Terminal")
zone_live = st.empty()

while True:
    try:
        # Récupération Prix et Solde
        ob = kraken.fetch_order_book('XRP/USDC', limit=1)
        p_ask = float(ob['asks'][0][0])
        p_bid = float(ob['bids'][0][0])
        prix_reel = (p_ask + p_bid) / 2
        
        balance = kraken.fetch_balance()
        usdc = balance.get('free', {}).get('USDC', balance.get('free', {}).get('ZUSD', 0))

        with zone_live.container():
            c1, c2, c3 = st.columns(3)
            c1.metric("SOLDE USDC", f"{usdc:,.2f} $")
            c2.metric("PRIX XRP LIVE", f"{prix_reel:.4f} $")
            total_gain = sum(b["gain"] for b in st.session_state.bots.values())
            c3.metric("GAINS CUMULÉS", f"+{total_gain:.4f} $")
            
            st.divider()
            
            # --- AFFICHAGE DES 10 ROBOTS (Correction des colonnes) ---
            # On crée 5 colonnes pour la première rangée
            row1 = st.columns(5)
            for i in range(5):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                with row1[i]:
                    st.write(f"### 🟡 {i+1}")
                    if bot["status"] == "ATTENTE_ACHAT":
                        st.warning(f"📥 ACHAT @{bot['p_achat']}")
                        info = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        if info['status'] == 'closed':
                            res_v = kraken.create_order('XRP/USDC', 'limit', 'sell', info['filled'], bot['p_vente'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res_v['id'], "status": "ATTENTE_VENTE"})
                            st.rerun()
                    elif bot["status"] == "ATTENTE_VENTE":
                        st.success(f"📤 VENTE @{bot['p_vente']}")
                        info_v = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        if info_v['status'] == 'closed':
                            profit_cycle = (bot['p_vente'] - bot['p_achat']) * info_v['filled']
                            st.session_state.bots[name]["gain"] += profit_cycle
                            st.session_state.bots[name]["cycles"] += 1
                            st.balloons()
                            qty = budget_input / bot['p_achat']
                            q = float(kraken.amount_to_precision('XRP/USDC', qty))
                            res_new = kraken.create_order('XRP/USDC', 'limit', 'buy', q, bot['p_achat'], {'validate': not mode_reel})
                            st.session_state.bots[name].update({"id": res_new['id'], "status": "ATTENTE_ACHAT"})
                            st.rerun()
                    st.write(f"🔄 {bot['cycles']} | 💰 {bot['gain']:.4f}$")

            # Deuxième rangée (Bots 6 à 10)
            row2 = st.columns(5)
            for i in range(5, 10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                with row2[i-5]:
                    st.write(f"### 🟡 {i+1}")
                    if bot["status"] == "ATTENTE_ACHAT":
                        st.warning(f"📥 ACHAT @{bot['p_achat']}")
                    elif bot["status"] == "ATTENTE_VENTE":
                        st.success(f"📤 VENTE @{bot['p_vente']}")
                    st.write(f"🔄 {bot['cycles']} | 💰 {bot['gain']:.4f}$")

    except Exception as e:
        if "Rate limit" in str(e): time.sleep(10)
        else: st.write(f"Flux... {e}")
    
    time.sleep(10)
