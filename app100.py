import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP BOT FINAL", layout="centered")

@st.cache_resource
def init_k():
    try:
        ex = ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
        })
        ex.nonce = lambda: ex.milliseconds()
        return ex
    except: return None

k = init_k()

# --- 2. MÉMOIRE DU BOT ---
if 'bot' not in st.session_state:
    st.session_state.bot = {"status": "OFF", "pa": 1.40, "pv": 1.45, "cycles": 0, "profit": 0.0}

bot = st.session_state.bot

# --- 3. DASHBOARD LIVE ---
try:
    ticker = k.fetch_ticker('XRP/USDC')
    px = ticker['last']
    bal = k.fetch_balance()
    usdc = bal['free'].get('USDC', 0.0)
    xrp = bal['free'].get('XRP', 0.0)
    
    st.title("🏓 XRP PING-PONG FINAL")
    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX XRP", f"{px:.4f}$")
    c2.metric("PROFIT NET", f"+{bot['profit']:.4f}$")
    c3.metric("CYCLES", bot["cycles"])
    
    st.info(f"💰 Portefeuille : **{usdc:.2f} USDC** | 🪙 **{xrp:.2f} XRP**")
except:
    st.error("Connexion Kraken interrompue.")
    st.stop()

st.divider()

# --- 4. RÉGLAGES ---
col1, col2 = st.columns(2)
pa = col1.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
pv = col2.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")

# --- 5. LOGIQUE BOUTONS ---
if bot["status"] == "OFF":
    if st.button("🚀 LANCER LE BOT (ALL-IN)", use_container_width=True, type="primary"):
        bot.update({"status": "ON", "pa": pa, "pv": pv})
        st.rerun()
else:
    if st.button("🛑 ARRÊTER ET TOUT ANNULER", use_container_width=True):
        try: k.cancel_all_orders('XRP/USDC')
        except: pass
        bot["status"] = "OFF"
        st.rerun()

# --- 6. MOTEUR DE SURVEILLANCE (FRAGMENT 15S) ---
if bot["status"] == "ON":
    @st.fragment(run_every=15)
    def engine():
        try:
            orders = k.fetch_open_orders('XRP/USDC')
            
            # SI AUCUN ORDRE -> ON EN CRÉE UN SELON LE SOLDE
            if not orders:
                bal_now = k.fetch_balance()
                u = bal_now['free'].get('USDC', 0.0)
                x = bal_now['free'].get('XRP', 0.0)
                
                if x > 5.0: # On a des XRP -> On place la VENTE
                    k.create_limit_sell_order('XRP/USDC', x, bot["pv"])
                    st.toast("✅ VENTE placée")
                    st.rerun()
                elif u > 7.0: # On a de l'USDC -> On place l'ACHAT
                    vol = float(k.amount_to_precision('XRP/USDC', u / bot["pa"]))
                    k.create_limit_buy_order('XRP/USDC', vol, bot["pa"], {'post-only': True})
                    st.toast("✅ ACHAT placé")
                    st.rerun()
            
            # Suivi visuel
            if orders:
                o = orders[-1]
                type_o = "ACHAT" if o['side'] == 'buy' else "VENTE"
                st.success(f"🤖 Bot actif : **{type_o}** à **{o['price']:.4f}$**")
                
                # Si une vente vient de se fermer, on calcule le profit (approximatif)
                if o['side'] == 'sell' and o['status'] == 'closed':
                    bot["profit"] += (bot["pv"] - bot["pa"]) * o['amount']
                    bot["cycles"] += 1
            
        except Exception as e:
            st.caption(f"Sync Kraken... {e}")

    engine()
