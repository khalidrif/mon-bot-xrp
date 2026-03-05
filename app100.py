import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP TARGET BOT", layout="centered")

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

# --- 2. MÉMOIRE ET SYNC ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", "pa": 1.4000, "pv": 1.4500, 
        "oid": None, "cycles": 0, "profit_total": 0.0, 
        "last_vol": 0.0, "last_price": 0.0
    }

def sync_active_order():
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

if st.session_state.bot["status"] == "OFF":
    if sync_active_order(): st.rerun()

st.title("🏓 XRP Ping-Pong")

# --- 3. AFFICHAGE DES CIBLES (PARTIE PRINCIPALE) ---
def draw_ui():
    try:
        ticker = kraken.fetch_ticker('XRP/USDC')
        px = ticker['last']
        bot = st.session_state.bot
        
        # En-tête : Prix actuel et Cycles
        c1, c2 = st.columns(2)
        c1.metric("🔥 PRIX XRP", f"{px:.4f} $")
        c2.metric("🔄 CYCLES RÉUSSIS", bot["cycles"])
        
        st.divider()

        # AFFICHAGE DE LA CIBLE ACTIVE
        if bot["status"] == "VENTE":
            diff = bot['pv'] - px
            st.subheader("🎯 CIBLE DE VENTE")
            st.metric("PRIX DE VENTE FIXÉ", f"{bot['pv']:.4f} $", delta=f"Reste {diff:.4f} $", delta_color="normal")
            st.progress(max(0.0, min(1.0, 1.0 - (diff / (bot['pv'] - bot['pa'])))) if (bot['pv']-bot['pa']) != 0 else 0.5)
            st.write(f"📦 Volume en vente : **{bot['last_vol']:.2f} XRP**")
            
        elif bot["status"] == "ACHAT":
            diff = px - bot['pa']
            st.subheader("🎯 CIBLE D'ACHAT")
            st.metric("PRIX D'ACHAT FIXÉ", f"{bot['pa']:.4f} $", delta=f"Reste {diff:.4f} $", delta_color="inverse")
            st.info("Le bot attend que le prix baisse pour racheter 'All-In'.")
            
        else:
            st.warning("⚠️ BOT À L'ARRÊT")

        st.divider()
        st.metric("📈 PROFIT NET TOTAL", f"+{bot['profit_total']:.4f} $")
            
    except: st.warning("Connexion Kraken...")

draw_ui()

# --- 4. RÉGLAGES ET BOUTONS ---
with st.expander("⚙️ MODIFIER LES PRIX CIBLES"):
    col_in, col_out = st.columns(2)
    new_pa = col_in.number_input("Prix Achat", value=st.session_state.bot["pa"], format="%.4f")
    new_pv = col_out.number_input("Prix Vente", value=st.session_state.bot["pv"], format="%.4f")
    if st.button("Mettre à jour les prix"):
        st.session_state.bot["pa"] = new_pa
        st.session_state.bot["pv"] = new_pv
        st.rerun()

if st.session_state.bot["status"] == "OFF":
    if st.button("🚀 DÉMARRER LE BOT", use_container_width=True, type="primary"):
        try:
            bal = kraken.fetch_balance()
            usdc = bal['free'].get('USDC', 0)
            vol = float(kraken.amount_to_precision('XRP/USDC', usdc / st.session_state.bot["pa"]))
            res = kraken.create_limit_buy_order('XRP/USDC', vol, st.session_state.bot["pa"], {'post-only': True})
            st.session_state.bot.update({"status": "ACHAT", "oid": res['id'], "last_vol": vol})
            st.rerun()
        except Exception as e: st.error(f"Erreur : {e}")
else:
    if st.button("🛑 ARRÊTER LE BOT", use_container_width=True):
        try:
            if st.session_state.bot["oid"]: kraken.cancel_order(st.session_state.bot["oid"])
        except: pass
        st.session_state.bot["status"] = "OFF"
        st.rerun()

# --- 5. MOTEUR ---
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
        except: pass
    engine()
