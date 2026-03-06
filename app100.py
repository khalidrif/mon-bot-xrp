import streamlit as st
import ccxt
import time

# 1. CONNEXION KRAKEN (DIRECTE)
try:
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
    # Correction pour éviter l'erreur de sécurité Kraken sur iPhone
    kraken.nonce = lambda: kraken.milliseconds()
except:
    st.error("🔑 Erreur de clés API dans les Secrets")

st.set_page_config(page_title="XRP SOLO PING-PONG", layout="centered")
st.title("🏓 XRP Solo Ping-Pong")

# --- BOUTON DE RESET TOTAL (DANS LA BARRE LATERALE) ---
if st.sidebar.button("🧹 RESET TOTAL (0 CYCLE / 0 PROFIT)"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 2. MÉMOIRE DU BOT
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", 
        "pa": 1.40, 
        "pv": 1.45, 
        "budget": 71.35, 
        "oid": None, 
        "cycles": 0, 
        "profit_total": 0.0
    }

# 3. RÉGLAGES DU CYCLE
with st.container():
    col1, col2, col3 = st.columns(3)
    p_achat = col1.number_input("PRIX ACHAT (IN)", value=st.session_state.bot["pa"], format="%.4f")
    p_vente = col2.number_input("PRIX VENTE (OUT)", value=st.session_state.bot["pv"], format="%.4f")
    budget = col3.number_input("BUDGET (USDC)", value=st.session_state.bot["budget"])

# 4. BOUTON START / STOP
if st.session_state.bot["status"] == "OFF":
    if st.button("🚀 DÉMARRER LE CYCLE INFINI", use_container_width=True, type="primary"):
        try:
            if not kraken.markets: kraken.load_markets()
            vol = float(kraken.amount_to_precision('XRP/USDC', budget / p_achat))
            res = kraken.create_limit_buy_order('XRP/USDC', vol, p_achat, {'post-only': True})
            st.session_state.bot.update({"status": "ACHAT", "pa": p_achat, "pv": p_vente, "budget": budget, "oid": res['id']})
            st.rerun()
        except Exception as e: st.error(f"Erreur : {e}")
else:
    if st.button("🛑 ARRÊTER LE BOT", use_container_width=True):
        try: kraken.cancel_order(st.session_state.bot["oid"])
        except: pass
        st.session_state.bot["status"] = "OFF"
        st.session_state.bot["oid"] = None
        st.rerun()

st.divider()

# 5. LOGIQUE DE BOUCLE AUTOMATIQUE
if st.session_state.bot["status"] != "OFF" and st.session_state.bot["oid"]:
    try:
        order = kraken.fetch_order(st.session_state.bot["oid"])
        
        if order['status'] == 'closed':
            if st.session_state.bot["status"] == "ACHAT":
                # VENTE
                vol_v = order['amount']
                res = kraken.create_limit_sell_order('XRP/USDC', vol_v, st.session_state.bot["pv"])
                st.session_state.bot.update({"status": "VENTE", "oid": res['id']})
                st.toast("✅ Achat OK ! Vente placée.")
            
            elif st.session_state.bot["status"] == "VENTE":
                # PROFIT + RELANCE
                profit = (st.session_state.bot["pv"] - st.session_state.bot["pa"]) * (st.session_state.bot["budget"] / st.session_state.bot["pa"])
                st.session_state.bot["profit_total"] += profit
                st.session_state.bot["cycles"] += 1
                
                vol_a = float(kraken.amount_to_precision('XRP/USDC', st.session_state.bot["budget"] / st.session_state.bot["pa"]))
                res = kraken.create_limit_buy_order('XRP/USDC', vol_a, st.session_state.bot["pa"], {'post-only': True})
                
                st.session_state.bot.update({"status": "ACHAT", "oid": res['id']})
                st.toast(f"💰 Cycle {st.session_state.bot['cycles']} terminé.")
            st.rerun()

    except Exception as e: st.caption(f"Synchronisation... {e}")

# 6. AFFICHAGE DES SCORES
try:
    ticker = kraken.fetch_ticker('XRP/USDC')
    px = ticker['last']
    c1, c2, c3 = st.columns(3)
    c1.metric("PRIX XRP", f"{px:.4f} $")
    c2.metric("STATUT", st.session_state.bot["status"])
    c3.metric("PROFIT", f"+{st.session_state.bot['profit_total']:.4f} $")
    st.info(f"📊 Cycles réussis : **{st.session_state.bot['cycles']}**")
except:
    st.write("Connexion Kraken...")

# RAFRAICHISSEMENT AUTO TOUTES LES 15 SECONDES
time.sleep(15)
st.rerun()
