import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ANTI-CRASH ---
st.set_page_config(page_title="XRP BOT 100% FIXED", layout="centered")

@st.cache_resource
def init_k():
    try:
        exchange = ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
        })
        exchange.nonce = lambda: exchange.milliseconds() # Fix InvalidNonce
        return exchange
    except Exception as e:
        st.error(f"Erreur Clés API : {e}")
        return None

k = init_k()

# --- 2. MÉMOIRE DU BOT ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", "pa": 1.40, "pv": 1.45, 
        "oid_buy": None, "oid_sell": None, 
        "cycles": 0, "profit": 0.0, "start_time": time.time()
    }

bot = st.session_state.bot

# --- 3. RÉCUPÉRATION DONNÉES (FORCE SYNC) ---
def get_data():
    try:
        ticker = k.fetch_ticker('XRP/USDC')
        bal = k.fetch_balance()
        return ticker['last'], bal
    except: return None, None

px, bal = get_data()

# --- 4. DASHBOARD ---
if bal:
    u_free = bal['total'].get('USDC', 0.0) # On utilise 'total' pour voir si l'argent est là
    x_free = bal['total'].get('XRP', 0.0)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🔥 XRP", f"{px:.4f}$")
    col2.metric("🔄 CYCLES", bot["cycles"])
    col3.metric("📈 PROFIT", f"{bot['profit']:.4f}$")
    
    st.write(f"💰 SOLDE : **{u_free:.2f} USDC** | 🪙 **{x_free:.2f} XRP**")
    st.divider()

    # --- 5. RÉGLAGES ---
    st.subheader("⚙️ Configuration")
    c_in, c_out = st.columns(2)
    new_pa = c_in.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
    new_pv = c_out.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")

    # --- 6. BOUTONS ACTION ---
    if bot["status"] == "OFF":
        if st.button("🚀 DÉMARRER / RÉINITIALISER", use_container_width=True, type="primary"):
            try:
                k.cancel_all_orders('XRP/USDC') # Nettoyage de sécurité
                bot.update({"status": "ON", "pa": new_pa, "pv": new_pv})
                
                # Check Achat
                if bal['free'].get('USDC', 0) > 5:
                    v_b = float(k.amount_to_precision('XRP/USDC', bal['free']['USDC'] / new_pa))
                    res_b = k.create_limit_buy_order('XRP/USDC', v_b, new_pa, {'post-only': True})
                    bot["oid_buy"] = res_b['id']
                
                # Check Vente
                if bal['free'].get('XRP', 0) > 5:
                    res_s = k.create_limit_sell_order('XRP/USDC', bal['free']['XRP'], new_pv)
                    bot["oid_sell"] = res_s['id']
                
                st.rerun()
            except Exception as e: st.error(f"Erreur Lancement : {e}")
    else:
        # BOUTONS QUAND LE BOT TOURNE
        if st.button("🔄 APPLIQUER NOUVEAUX PRIX", use_container_width=True):
            try:
                k.cancel_all_orders('XRP/USDC')
                bot.update({"pa": new_pa, "pv": new_pv, "oid_buy": None, "oid_sell": None})
                st.rerun()
            except: pass

        if st.button("🛑 ARRÊTER TOUT", use_container_width=True, type="secondary"):
            try: k.cancel_all_orders('XRP/USDC')
            except: pass
            bot["status"] = "OFF"
            st.rerun()

    # --- 7. MOTEUR DE SURVEILLANCE ---
    if bot["status"] == "ON":
        @st.fragment(run_every=15)
        def engine():
            try:
                # Si aucun ordre n'est actif, on en crée un basé sur le solde
                if not bot["oid_buy"] and not bot["oid_sell"]:
                    bal_now = k.fetch_balance()
                    if bal_now['free'].get('USDC', 0) > 5:
                        v = float(k.amount_to_precision('XRP/USDC', bal_now['free']['USDC'] / bot["pa"]))
                        res = k.create_limit_buy_order('XRP/USDC', v, bot["pa"], {'post-only': True})
                        bot["oid_buy"] = res['id']
                    elif bal_now['free'].get('XRP', 0) > 5:
                        res = k.create_limit_sell_order('XRP/USDC', bal_now['free']['XRP'], bot["pv"])
                        bot["oid_sell"] = res['id']
                    st.rerun()

                # Vérification Achat
                if bot["oid_buy"]:
                    o = k.fetch_order(bot["oid_buy"], 'XRP/USDC')
                    if o['status'] == 'closed':
                        bot["oid_buy"] = None
                        st.rerun()

                # Vérification Vente
                if bot["oid_sell"]:
                    o = k.fetch_order(bot["oid_sell"], 'XRP/USDC')
                    if o['status'] == 'closed':
                        bot["profit"] += (bot["pv"] - bot["pa"]) * o['filled']
                        bot["cycles"] += 1
                        bot["oid_sell"] = None
                        st.rerun()
            except: pass
        engine()

else:
    st.warning("🔄 Connexion à Kraken... Vérifiez vos clés API dans les Secrets.")
    time.sleep(5)
    st.rerun()
