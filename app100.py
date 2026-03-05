import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP SYNC MASTER", layout="centered")

@st.cache_resource
def init_k():
    try:
        return ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True
        })
    except: return None

k = init_k()

# --- 2. MÉMOIRE ET RÉCUPÉRATION ---
if 'bot' not in st.session_state:
    st.session_state.bot = {"status": "OFF", "pa": 1.40, "pv": 1.45, "oid": None, "cycles": 0, "profit": 0.0, "vol": 0.0}
    try:
        # Synchro auto au chargement de la page iPhone
        orders = k.fetch_open_orders('XRP/USDC')
        if orders:
            o = orders[-1]
            st.session_state.bot.update({
                "status": "ACHAT" if o['side']=='buy' else "VENTE", 
                "oid": o['id'], "vol": o['amount'], "pa": o['price'] if o['side']=='buy' else 1.40
            })
    except: pass

bot = st.session_state.bot

# --- 3. DASHBOARD ---
ticker = k.fetch_ticker('XRP/USDC')
px = ticker['last']
bal = k.fetch_balance()
u_free = bal['free'].get('USDC', 0.0)
x_free = bal['free'].get('XRP', 0.0)

c1, c2 = st.columns(2)
c1.metric("🔥 XRP LIVE", f"{px:.4f}$")
c2.metric("🔄 CYCLES", bot["cycles"])

st.write(f"💰 {u_free:.2f} USDC | 🪙 {x_free:.2f} XRP")
st.divider()

# --- 4. CONTRÔLE DYNAMIQUE ---
if bot["status"] != "OFF":
    target = bot["pa"] if bot["status"] == "ACHAT" else bot["pv"]
    st.success(f"🎯 **ORDRE {bot['status']} ACTIF**")
    st.metric("PRIX CIBLE", f"{target:.4f}$", delta=f"{target - px:.4f}$")
    st.write(f"Volume : **{bot['vol']:.2f} XRP**")
    
    # BOUTON ARRÊTER AVEC ANNULATION KRAKEN
    if st.button("🛑 ARRÊTER ET ANNULER L'ORDRE", use_container_width=True, type="primary"):
        try:
            if bot["oid"]:
                k.cancel_order(bot["oid"]) # ANNULATION RÉELLE SUR KRAKEN
                st.toast("✅ Ordre annulé sur Kraken !")
        except Exception as e:
            st.error(f"Erreur annulation : {e}")
        
        bot["status"] = "OFF"
        bot["oid"] = None
        st.rerun()
else:
    # REGLAGES START
    col_in, col_out = st.columns(2)
    pa_in = col_in.number_input("PRIX ACHAT (IN)", value=bot["pa"], format="%.4f")
    pv_out = col_out.number_input("PRIX VENTE (OUT)", value=bot["pv"], format="%.4f")

    if st.button("🚀 DÉMARRER LE BOT", use_container_width=True, type="primary"):
        # Détection automatique de ce qu'il faut faire
        if x_free > 1: # On a des XRP -> Vente
            res = k.create_limit_sell_order('XRP/USDC', x_free, pv_out)
            bot.update({"status": "VENTE", "pa": pa_in, "pv": pv_out, "oid": res['id'], "vol": x_free})
        elif u_free > 5: # On a de l'USDC -> Achat
            v = float(k.amount_to_precision('XRP/USDC', u_free / pa_in))
            res = k.create_limit_buy_order('XRP/USDC', v, pa_in, {'post-only': True})
            bot.update({"status": "ACHAT", "pa": pa_in, "pv": pv_out, "oid": res['id'], "vol": v})
        st.rerun()

# --- 5. ENGINE ---
if bot["status"] != "OFF":
    @st.fragment(run_every=15)
    def engine():
        try:
            o = k.fetch_order(bot["oid"], 'XRP/USDC')
            if o['status'] == 'closed':
                if bot["status"] == "ACHAT":
                    res = k.create_limit_sell_order('XRP/USDC', o['filled'], bot["pv"])
                    bot.update({"status": "VENTE", "oid": res['id'], "vol": o['filled']})
                else:
                    bot["profit"] += (bot["pv"] - bot["pa"]) * o['filled']
                    bot["cycles"] += 1
                    bal_s = k.fetch_balance()
                    v_s = float(k.amount_to_precision('XRP/USDC', bal_s['free'].get('USDC', 0) / bot["pa"]))
                    res = k.create_limit_buy_order('XRP/USDC', v_s, bot["pa"], {'post-only': True})
                    bot.update({"status": "ACHAT", "oid": res['id'], "vol": v_s})
                st.rerun()
        except: pass
    engine()
