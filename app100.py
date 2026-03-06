import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ANTI-CRASH ---
st.set_page_config(page_title="XRP BOT SYNC", layout="centered")

@st.cache_resource
def init_k():
    try:
        exchange = ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
        })
        # CORRECTIF CRUCIAL POUR IPHONE ET INVALID NONCE
        exchange.nonce = lambda: exchange.milliseconds()
        return exchange
    except: return None

k = init_k()

# --- 2. MÉMOIRE DU BOT ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", "pa": 1.40, "pv": 1.45, 
        "oid_buy": None, "oid_sell": None, 
        "cycles": 0, "profit": 0.0, "start_time": time.time()
    }

bot = st.session_state.bot

# --- 3. RÉCUPÉRATION DONNÉES ---
def get_kraken_data():
    try:
        ticker = k.fetch_ticker('XRP/USDC')
        bal = k.fetch_balance()
        return ticker['last'], bal
    except: return None, None

px, bal = get_kraken_data()

# --- 4. DASHBOARD ---
if bal:
    u_free = bal['free'].get('USDC', 0.0)
    x_free = bal['free'].get('XRP', 0.0)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 XRP", f"{px:.4f}$")
    c2.metric("📈 PROFIT", f"{bot['profit']:.4f}$")
    c3.metric("🔄 CYCLES", bot["cycles"])
    st.write(f"💰 {u_free:.2f} USDC | 🪙 {x_free:.2f} XRP")
    st.divider()

    # --- 5. RÉGLAGES DYNAMIQUES ---
    st.subheader("⚙️ Modifier la fourchette")
    col_in, col_out = st.columns(2)
    new_pa = col_in.number_input("ACHAT (IN)", value=bot["pa"], format="%.4f")
    new_pv = col_out.number_input("VENTE (OUT)", value=bot["pv"], format="%.4f")

    # BOUTON DE MISE À JOUR (Apparaît si les prix changent)
    if bot["status"] == "ON" and (new_pa != bot["pa"] or new_pv != bot["pv"]):
        if st.button("🔄 APPLIQUER MODIFS", use_container_width=True, type="primary"):
            try:
                k.cancel_all_orders('XRP/USDC') # Nettoyage Kraken
                time.sleep(0.5)
                # Repose l'achat
                oid_b = None
                if u_free > 5:
                    v_b = float(k.amount_to_precision('XRP/USDC', u_free / new_pa))
                    res_b = k.create_limit_buy_order('XRP/USDC', v_b, new_pa, {'post-only': True})
                    oid_b = res_b['id']
                # Repose la vente
                oid_s = None
                if x_free > 5:
                    res_s = k.create_limit_sell_order('XRP/USDC', x_free, new_pv)
                    oid_s = res_s['id']
                
                bot.update({"pa": new_pa, "pv": new_pv, "oid_buy": oid_b, "oid_sell": oid_s})
                st.toast("✅ Prix mis à jour sur Kraken !")
                st.rerun()
            except Exception as e: st.error(f"Erreur MAJ: {e}")

    # --- 6. START / STOP ---
    if bot["status"] == "OFF":
        if st.button("🚀 DÉMARRER LE BOT", use_container_width=True, type="primary"):
            try:
                bot.update({"status": "ON", "pa": new_pa, "pv": new_pv})
                oid_b, oid_s = None, None
                if u_free > 5:
                    v_b = float(k.amount_to_precision('XRP/USDC', u_free / new_pa))
                    res_b = k.create_limit_buy_order('XRP/USDC', v_b, new_pa, {'post-only': True})
                    oid_b = res_b['id']
                if x_free > 5:
                    res_s = k.create_limit_sell_order('XRP/USDC', x_free, new_pv)
                    oid_s = res_s['id']
                bot.update({"oid_buy": oid_b, "oid_sell": oid_s})
                st.rerun()
            except Exception as e: st.error(f"Erreur : {e}")
    else:
        if st.button("🛑 ARRÊTER ET ANNULER", use_container_width=True):
            try: k.cancel_all_orders('XRP/USDC')
            except: pass
            bot.update({"status": "OFF", "oid_buy": None, "oid_sell": None})
            st.rerun()

    # --- 7. MOTEUR SÉCURISÉ ---
    if bot["status"] == "ON":
        @st.fragment(run_every=15)
        def engine():
            try:
                if bot["oid_buy"]:
                    o_b = k.fetch_order(bot["oid_buy"], 'XRP/USDC')
                    if o_b['status'] == 'closed':
                        k.cancel_all_orders('XRP/USDC')
                        bal_n = k.fetch_balance()
                        res_s = k.create_limit_sell_order('XRP/USDC', bal_n['free'].get('XRP', 0), bot["pv"])
                        bot.update({"oid_buy": None, "oid_sell": res_s['id']})
                        st.rerun()
                if bot["oid_sell"]:
                    o_s = k.fetch_order(bot["oid_sell"], 'XRP/USDC')
                    if o_s['status'] == 'closed':
                        bot["profit"] += (bot["pv"] - bot["pa"]) * o_s['filled']
                        bot["cycles"] += 1
                        k.cancel_all_orders('XRP/USDC')
                        bal_n = k.fetch_balance()
                        v_new = float(k.amount_to_precision('XRP/USDC', bal_n['free'].get('USDC', 0) / bot["pa"]))
                        res_b = k.create_limit_buy_order('XRP/USDC', v_new, bot["pa"], {'post-only': True})
                        bot.update({"oid_buy": res_b['id'], "oid_sell": None})
                        st.rerun()
            except: pass
        engine()
else:
    st.warning("🔄 Tentative de connexion à Kraken...")
    time.sleep(2)
    st.rerun()
