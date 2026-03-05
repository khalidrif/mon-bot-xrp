import streamlit as st
import ccxt
import time
from datetime import datetime

# --- 1. CONFIGURATION ET CONNEXION ---
st.set_page_config(page_title="XRP MAX-PROFIT BOT", layout="centered")

@st.cache_resource
def init_kraken():
    try:
        return ccxt.kraken({
            'apiKey': st.secrets["KRAKEN_KEY"],
            'secret': st.secrets["KRAKEN_SECRET"],
            'enableRateLimit': True,
        })
    except Exception as e:
        st.error(f"Erreur API : {e}")
        return None

kraken = init_kraken()

# --- 2. MÉMOIRE DU BOT ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", "pa": 1.4000, "pv": 1.4500, 
        "oid": None, "cycles": 0, "profit_total": 0.0, 
        "last_vol": 0.0, "start_time": None, "last_price": 0.0
    }

st.title("🏓 XRP Ping-Pong Live")

# --- 3. DASHBOARD (SOLDES + PRIX LIVE) ---
def show_dashboard():
    try:
        # Récupération Prix XRP Live
        ticker = kraken.fetch_ticker('XRP/USDC')
        current_px = ticker['last']
        change = current_px - st.session_state.bot["last_price"] if st.session_state.bot["last_price"] > 0 else 0
        st.session_state.bot["last_price"] = current_px

        # Récupération Soldes
        bal = kraken.fetch_balance()
        usdc_free = bal['free'].get('USDC', 0.0)
        xrp_free = bal['free'].get('XRP', 0.0)
        
        # Affichage Métriques
        col_p1, col_p2 = st.columns(2)
        col_p1.metric("🔥 PRIX XRP LIVE", f"{current_px:.4f} $", delta=f"{change:.4f}$")
        col_p2.metric("📈 PROFIT CUMULÉ", f"+{st.session_state.bot['profit_total']:.4f} $")

        st.divider()
        
        c1, c2 = st.columns(2)
        c1.write(f"**💰 Disponible :** {usdc_free:.2f} USDC")
        c2.write(f"**🪙 En attente :** {xrp_free:.2f} XRP")

    except Exception as e:
        st.caption(f"Calcul des données... {e}")

show_dashboard()

# --- 4. RÉGLAGES ---
with st.expander("⚙️ RÉGLAGES DES BORNES", expanded=(st.session_state.bot["status"] == "OFF")):
    col_in, col_out = st.columns(2)
    p_achat = col_in.number_input("ACHAT À", value=st.session_state.bot["pa"], format="%.4f")
    p_vente = col_out.number_input("VENTE À", value=st.session_state.bot["pv"], format="%.4f")

# --- 5. CONTRÔLE ---
if st.session_state.bot["status"] == "OFF":
    if st.button("🚀 DÉMARRER (ALL-IN REINVEST)", use_container_width=True, type="primary"):
        try:
            bal = kraken.fetch_balance()
            usdc_dispo = bal['free'].get('USDC', 0.0)
            if usdc_dispo < 5:
                st.error("Solde USDC insuffisant (Min 5$)")
            else:
                vol = float(kraken.amount_to_precision('XRP/USDC', usdc_dispo / p_achat))
                res = kraken.create_limit_buy_order('XRP/USDC', vol, p_achat, {'post-only': True})
                st.session_state.bot.update({
                    "status": "ACHAT", "pa": p_achat, "pv": p_vente, 
                    "oid": res['id'], "last_vol": vol, "start_time": time.time()
                })
                st.rerun()
        except Exception as e: st.error(f"Erreur Start : {e}")
else:
    if st.button("🛑 ARRÊTER LE BOT", use_container_width=True):
        try:
            if st.session_state.bot["oid"]: kraken.cancel_order(st.session_state.bot["oid"])
        except: pass
        st.session_state.bot["status"] = "OFF"
        st.rerun()

# --- 6. LE MOTEUR (FRAGMENT 15S) ---
if st.session_state.bot["status"] != "OFF":
    @st.fragment(run_every=15)
    def engine():
        bot = st.session_state.bot
        try:
            # Synchro avec Kraken
            order = kraken.fetch_order(bot["oid"], 'XRP/USDC')
            
            if order['status'] == 'closed':
                if bot["status"] == "ACHAT":
                    # L'achat est passé -> Vendre tout
                    res = kraken.create_limit_sell_order('XRP/USDC', order['filled'], bot["pv"])
                    st.session_state.bot.update({"status": "VENTE", "oid": res['id'], "last_vol": order['filled']})
                    st.rerun()
                
                elif bot["status"] == "VENTE":
                    # La vente est passée -> Recommencer All-In
                    st.session_state.bot["profit_total"] += (bot["pv"] - bot["pa"]) * order['filled']
                    st.session_state.bot["cycles"] += 1
                    
                    bal = kraken.fetch_balance()
                    usdc_nouveau = bal['free'].get('USDC', 0.0)
                    vol_nouveau = float(kraken.amount_to_precision('XRP/USDC', usdc_nouveau / bot["pa"]))
                    res = kraken.create_limit_buy_order('XRP/USDC', vol_nouveau, bot["pa"], {'post-only': True})
                    st.session_state.bot.update({"status": "ACHAT", "oid": res['id'], "last_vol": vol_nouveau})
                    st.rerun()

            # État visuel
            st.info(f"🤖 **{bot['status']} EN COURS** | {bot['last_vol']:.2f} XRP à {bot['pa'] if bot['status'] == 'ACHAT' else bot['pv']}$")
            st.caption(f"Dernière synchro : {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            st.caption(f"Recherche de l'ordre... {e}")

    engine()
