import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP BOT 100%", layout="centered")

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

# --- 2. MÉMOIRE ET SYNC AUTO (IPHONE RECOVERY) ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", "pa": 1.4000, "pv": 1.4500, 
        "oid": None, "cycles": 0, "profit": 0.0, 
        "vol": 0.0, "start_time": time.time()
    }
    # Scan immédiat au chargement pour retrouver un ordre ouvert
    try:
        orders = k.fetch_open_orders('XRP/USDC')
        if orders:
            o = orders[-1]
            st.session_state.bot.update({
                "status": "ACHAT" if o['side'] == 'buy' else "VENTE",
                "oid": o['id'],
                "vol": o['amount'],
                "pa": o['price'] if o['side'] == 'buy' else 1.4000,
                "pv": o['price'] if o['side'] == 'sell' else 1.4500
            })
    except: pass

bot = st.session_state.bot

# --- 3. INTERFACE (DASHBOARD) ---
st.title("🏓 XRP Ping-Pong 100%")

try:
    ticker = k.fetch_ticker('XRP/USDC')
    px = ticker['last']
    bal = k.fetch_balance()
    u_free = bal['free'].get('USDC', 0.0)
    x_free = bal['free'].get('XRP', 0.0)

    # Ligne 1 : Prix et Profit
    c1, c2 = st.columns(2)
    c1.metric("🔥 PRIX XRP", f"{px:.4f} $")
    c2.metric("📈 PROFIT NET", f"+{bot['profit']:.4f} $")

    # Ligne 2 : Cycles et Portefeuille
    c3, c4 = st.columns(2)
    c3.metric("🔄 CYCLES", bot["cycles"])
    c4.write(f"💰 **{u_free:.2f}** USDC | 🪙 **{x_free:.2f}** XRP")

    st.divider()

    # SECTION CIBLE ACTIVE
    if bot["status"] != "OFF":
        target = bot["pa"] if bot["status"] == "ACHAT" else bot["pv"]
        diff = abs(target - px)
        color = "blue" if bot["status"] == "VENTE" else "orange"
        
        st.subheader(f"🎯 CIBLE {bot['status']}")
        st.metric(f"PRIX VISÉ ({bot['status']})", f"{target:.4f} $", 
                  delta=f"Distance: {diff:.4f} $", 
                  delta_color="normal" if bot["status"]=="VENTE" else "inverse")
        
        if st.button("🛑 ARRÊTER LE BOT", use_container_width=True, type="secondary"):
            try: k.cancel_order(bot["oid"])
            except: pass
            bot["status"] = "OFF"
            st.rerun()
    else:
        # RÉGLAGES SI OFF
        st.info("Configuration du cycle All-In")
        col_in, col_out = st.columns(2)
        pa_input = col_in.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
        pv_input = col_out.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")
        
        if st.button("🚀 DÉMARRER LE BOT", use_container_width=True, type="primary"):
            if u_free < 5:
                st.error("Solde USDC insuffisant (Min 5$)")
            else:
                v = float(k.amount_to_precision('XRP/USDC', u_free / pa_input))
                res = k.create_limit_buy_order('XRP/USDC', v, pa_input, {'post-only': True})
                bot.update({"status": "ACHAT", "pa": pa_input, "pv": pv_input, "oid": res['id'], "vol": v})
                st.rerun()

except Exception as e:
    st.error(f"⚠️ Erreur de connexion Kraken : {e}")

# --- 4. LE MOTEUR (FRAGMENT 15S) ---
if bot["status"] != "OFF":
    @st.fragment(run_every=15)
    def engine():
        try:
            o = k.fetch_order(bot["oid"], 'XRP/USDC')
            if o['status'] == 'closed':
                if bot["status"] == "ACHAT":
                    # ACHAT FINI -> VENTE
                    res = k.create_limit_sell_order('XRP/USDC', o['filled'], bot["pv"])
                    bot.update({"status": "VENTE", "oid": res['id'], "vol": o['filled']})
                    st.rerun()
                elif bot["status"] == "VENTE":
                    # VENTE FINIE -> PROFIT -> RE-ACHAT ALL-IN
                    bot["profit"] += (bot["pv"] - bot["pa"]) * o['filled']
                    bot["cycles"] += 1
                    bal_sync = k.fetch_balance()
                    v_new = float(k.amount_to_precision('XRP/USDC', bal_sync['free'].get('USDC', 0) / bot["pa"]))
                    res = k.create_limit_buy_order('XRP/USDC', v_new, bot["pa"], {'post-only': True})
                    bot.update({"status": "ACHAT", "oid": res['id'], "vol": v_new})
                    st.rerun()
            
            st.caption(f"Dernière synchro : {datetime.now().strftime('%H:%M:%S')}")
        except: pass

    engine()
