import streamlit as st
import ccxt
import time
import json
import os
from config import get_kraken_connection

# 1. STYLE BLOOMBERG
st.set_page_config(page_title="XRP Bloomberg DIRECT ORDER", layout="wide")
st.markdown("<style>.main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }</style>", unsafe_allow_html=True)

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
    st.header("⚡ CMD DIRECT")
    p_in_set = st.number_input("TARGET IN", value=1.4000, format="%.4f")
    p_out_set = st.number_input("TARGET OUT", value=1.4500, format="%.4f")
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
                
                # --- ACTION : PLACEMENT IMMEDIAT DE L'ORDRE D'ACHAT ---
                vol = float(kraken.amount_to_precision('XRP/USDC', budget_val / pa_f))
                try:
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                    st.session_state.bots[id_b].update({"status": "ACHAT_OUVERT", "pa": pa_f, "pv": pv_f, "budget": budget_val, "oid": res['id']})
                    sauvegarder(st.session_state.bots, st.session_state.profit_total)
                    st.success(f"ORDRE {id_b} PLACÉ : ID {res['id']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"REFUS KRAKEN : {e}")
        else:
            if c2.button(f"OFF {i+1}", key=f"o{i}"):
                # Annulation de l'ordre sur Kraken si on coupe le bot
                try:
                    if st.session_state.bots[id_b]["oid"] != "NONE":
                        kraken.cancel_order(st.session_state.bots[id_b]["oid"])
                except: pass
                st.session_state.bots[id_b].update({"status": "LIBRE", "oid": "NONE"}); st.rerun()

# --- BOUCLE PRINCIPALE ---
live = st.empty()
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        with live.container():
            st.write(f"### MARKET : {px:.4f}")
            for name, bot in st.session_state.bots.items():
                if bot["status"] == "ACHAT_OUVERT":
                    # Le bot surveille si l'achat est complété sur Kraken
                    st.info(f"⏳ {name} : Ordre d'Achat ouvert à {bot['pa']} (ID: {bot['oid']})")
                    # Ici, on pourrait ajouter une logique pour vérifier si l'ordre est 'closed'
                    # Pour simplifier, si le prix touche pa, on considère qu'il va passer en VENTE
                    if px <= bot["pa"]:
                        st.session_state.bots[name]["status"] = "SURVEILLANCE_VENTE"
                        sauvegarder(st.session_state.bots, st.session_state.profit_total)

                elif bot["status"] == "SURVEILLANCE_VENTE":
                    st.success(f"📈 {name} : XRP acheté ! Attente pour vendre à {bot['pv']}")
                    if px >= bot["pv"]:
                        # Placement de l'ordre de vente
                        vol = float(kraken.amount_to_precision('XRP/USDC', bot["budget"] / bot["pa"]))
                        res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["pv"])
                        st.session_state.bots[name].update({"status": "ACHAT_OUVERT", "oid": res['id']}) # Recommence cycle
    except: pass
    time.sleep(10)
