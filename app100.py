import streamlit as st
import ccxt
import time
from datetime import datetime

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="XRP ALL-IN PING-PONG", layout="centered")

# --- 1. CONNEXION KRAKEN ---
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

# --- 2. ÉTAT DU BOT (MÉMOIRE) ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", "pa": 1.40, "pv": 1.45, 
        "oid": None, "cycles": 0, "profit_total": 0.0, 
        "last_vol": 0.0, "start_time": None
    }

st.title("🏓 XRP Solo Ping-Pong")

# --- 3. AFFICHAGE DES SOLDES ET GAINS ---
def show_metrics():
    try:
        # Récupération Soldes
        bal = kraken.fetch_balance()
        usdc_free = bal['free'].get('USDC', 0.0)
        xrp_free = bal['free'].get('XRP', 0.0)
        
        # Calcul Profit Journalier
        profit_total = st.session_state.bot["profit_total"]
        gain_jour = 0.0
        if st.session_state.bot["status"] != "OFF" and st.session_state.bot["start_time"]:
            diff_secondes = time.time() - st.session_state.bot["start_time"]
            jours_ecoules = diff_secondes / 86400
            if jours_ecoules > 0:
                gain_jour = profit_total / jours_ecoules

        # Affichage
        c1, c2 = st.columns(2)
        c1.metric("SOLDE USDC", f"{usdc_free:.2f} $")
        c2.metric("SOLDE XRP", f"{xrp_free:.2f} XRP")
        
        g1, g2 = st.columns(2)
        g1.metric("NET PROFIT TOTAL", f"+{profit_total:.4f} $", delta_color="normal")
        g2.metric("GAIN EST. / JOUR", f"{gain_jour:.2f} $")
        
    except:
        st.warning("Chargement des données Kraken...")

show_metrics()
st.divider()

# --- 4. RÉGLAGES ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    p_achat = col1.number_input("PRIX ACHAT", value=st.session_state.bot["pa"], format="%.4f")
    p_vente = col2.number_input("PRIX VENTE", value=st.session_state.bot["pv"], format="%.4f")

# --- 5. CONTRÔLE ---
if st.session_state.bot["status"] == "OFF":
    if st.button("🚀 LANCER LE BOT (ALL-IN)", use_container_width=True, type="primary"):
        try:
            bal = kraken.fetch_balance()
            usdc_dispo = bal['free'].get('USDC', 0)
            if usdc_dispo < 5:
                st.error(f"Solde USDC trop faible ({usdc_dispo:.2f})")
            else:
                vol = float(kraken.amount_to_precision('XRP/USDC', usdc_dispo / p_achat))
                res = kraken.create_limit_buy_order('XRP/USDC', vol, p_achat, {'post-only': True})
                st.session_state.bot.update({
                    "status": "ACHAT", "pa": p_achat, "pv": p_vente, 
                    "oid": res['id'], "last_vol": vol, 
                    "start_time": time.time() # On note l'heure de début
                })
                st.rerun()
        except Exception as e: st.error(f"Erreur : {e}")
else:
    if st.button("🛑 ARRÊTER LE BOT", use_container_width=True):
        try: kraken.cancel_order(st.session_state.bot["oid"])
        except: pass
        st.session_state.bot["status"] = "OFF"
        st.rerun()

# --- 6. MOTEUR DE TRADING (FRAGMENT 15S) ---
if st.session_state.bot["status"] != "OFF":
    @st.fragment(run_every=15)
    def trading_engine():
        bot = st.session_state.bot
        try:
            order = kraken.fetch_order(bot["oid"], 'XRP/USDC')
            
            if order['status'] == 'closed':
                if bot["status"] == "ACHAT":
                    # Passage à la vente
                    vol_vendu = order['filled']
                    res = kraken.create_limit_sell_order('XRP/USDC', vol_vendu, bot["pv"])
                    st.session_state.bot.update({"status": "VENTE", "oid": res['id'], "last_vol": vol_vendu})
                
                elif bot["status"] == "VENTE":
                    # Profit & Relance
                    st.session_state.bot["profit_total"] += (bot["pv"] - bot["pa"]) * order['filled']
                    st.session_state.bot["cycles"] += 1
                    
                    bal = kraken.fetch_balance()
                    usdc_dispo = bal['free'].get('USDC', 0)
                    vol_a = float(kraken.amount_to_precision('XRP/USDC', usdc_dispo / bot["pa"]))
                    res = kraken.create_limit_buy_order('XRP/USDC', vol_a, bot["pa"], {'post-only': True})
                    st.session_state.bot.update({"status": "ACHAT", "oid": res['id'], "last_vol": vol_a})
                st.rerun()

            # Infos de suivi
            ticker = kraken.fetch_ticker('XRP/USDC')
            st.info(f"🤖 **{bot['status']} EN COURS** | Prix XRP: **{ticker['last']:.4f}** | Cycles: **{bot['cycles']}**")
            st.caption(f"Dernier check : {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            st.caption(f"Synchro... {e}")

    trading_engine()
