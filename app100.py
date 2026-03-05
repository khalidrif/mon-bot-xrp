import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP BOT 100% SYNC", layout="centered")

@st.cache_resource
def init_kraken():
    try:
        return ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
        })
    except: return None

kraken = init_kraken()

# --- 2. MÉMOIRE ET SYNCHRONISATION ANALYTIQUE ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", "pa": 1.4000, "pv": 1.4500, 
        "oid": None, "cycles": 0, "profit_total": 0.0, 
        "last_vol": 0.0, "start_time": time.time(), "last_price": 0.0
    }

# CERVEAU DE RÉCUPÉRATION (Force le bouton ARRÊTER si un ordre existe sur Kraken)
def sync_with_kraken():
    try:
        open_orders = kraken.fetch_open_orders('XRP/USDC')
        if open_orders:
            last = open_orders[-1]
            st.session_state.bot.update({
                "status": "ACHAT" if last['side'] == 'buy' else "VENTE",
                "oid": last['id'],
                "last_vol": last['amount'],
                "pa": last['price'] if last['side'] == 'buy' else st.session_state.bot["pa"],
                "pv": last['price'] if last['side'] == 'sell' else st.session_state.bot["pv"]
            })
            return True
    except: pass
    return False

# Lancer la synchro au chargement de la page
if st.session_state.bot["status"] == "OFF":
    sync_with_kraken()

st.title("🏓 XRP Ping-Pong (iPhone Sync)")

# --- 3. DASHBOARD LIVE ---
def draw_ui():
    try:
        ticker = kraken.fetch_ticker('XRP/USDC')
        px = ticker['last']
        bal = kraken.fetch_balance()
        
        c1, c2 = st.columns(2)
        c1.metric("🔥 PRIX XRP", f"{px:.4f} $")
        c2.metric("📈 PROFIT", f"+{st.session_state.bot['profit_total']:.4f} $")
        
        st.info(f"💰 USDC: **{bal['free'].get('USDC', 0):.2f}** | 🪙 XRP: **{bal['free'].get('XRP', 0):.2f}**")
    except: st.warning("Connexion Kraken...")

draw_ui()

# --- 4. RÉGLAGES ---
with st.expander("⚙️ PARAMÈTRES", expanded=(st.session_state.bot["status"] == "OFF")):
    col_in, col_out = st.columns(2)
    p_achat = col_in.number_input("ACHAT À", value=st.session_state.bot["pa"], format="%.4f")
    p_vente = col_out.number_input("VENTE À", value=st.session_state.bot["pv"], format="%.4f")

# --- 5. BOUTONS ---
if st.session_state.bot["status"] == "OFF":
    if st.button("🚀 DÉMARRER LE BOT", use_container_width=True, type="primary"):
        try:
            bal = kraken.fetch_balance()
            usdc = bal['free'].get('USDC', 0)
            vol = float(kraken.amount_to_precision('XRP/USDC', usdc / p_achat))
            res = kraken.create_limit_buy_order('XRP/USDC', vol, p_achat, {'post-only': True})
            st.session_state.bot.update({"status": "ACHAT", "pa": p_achat, "pv": p_vente, "oid": res['id'], "last_vol": vol})
            st.rerun()
        except Exception as e: st.error(f"Erreur : {e}")
else:
    if st.button("🛑 ARRÊTER LE BOT", use_container_width=True):
        try:
            kraken.cancel_order(st.session_state.bot["oid"])
        except: pass
        st.session_state.bot["status"] = "OFF"
        st.session_state.bot["oid"] = None
        st.rerun()

# --- 6. MOTEUR (FRAGMENT) ---
if st.session_state.bot["status"] != "OFF":
    @st.fragment(run_every=15)
    def engine():
        bot = st.session_state.bot
        try:
            order = kraken.fetch_order(bot["oid"], 'XRP/USDC')
            if order['status'] == 'closed':
                if bot["status"] == "ACHAT":
                    res = kraken.create_limit_sell_order('XRP/USDC', order['filled'], bot["pv"])
                    st.session_state.bot.update({"status": "VENTE", "oid": res['id'], "last_vol": order['filled']})
                    st.rerun()
                elif bot["status"] == "VENTE":
                    st.session_state.bot["profit_total"] += (bot["pv"] - bot["pa"]) * order['filled']
                    st.session_state.bot["cycles"] += 1
                    bal = kraken.fetch_balance()
                    vol = float(kraken.amount_to_precision('XRP/USDC', bal['free'].get('USDC', 0) / bot["pa"]))
                    res = kraken.create_limit_buy_order('XRP/USDC', vol, bot["pa"], {'post-only': True})
                    st.session_state.bot.update({"status": "ACHAT", "oid": res['id'], "last_vol": vol})
                    st.rerun()
            st.success(f"🤖 BOT EN ACTION ({bot['status']})")
            st.caption(f"Dernier check : {datetime.now().strftime('%H:%M:%S')}")
        except: st.caption("Recherche de l'ordre...")

    engine()
