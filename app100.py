import streamlit as st
import ccxt
import time
from datetime import datetime

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="XRP MAX-PROFIT BOT", layout="centered")

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

# --- 2. MÉMOIRE DU BOT ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", "pa": 1.40, "pv": 1.45, 
        "oid": None, "cycles": 0, "profit_total": 0.0, 
        "last_vol": 0.0, "start_time": None
    }

st.title("🏓 XRP Ping-Pong (Auto-Reinvest)")

# --- 3. AFFICHAGE DES MÉTRIQUES ---
def show_metrics():
    try:
        bal = kraken.fetch_balance()
        usdc_free = bal['free'].get('USDC', 0.0)
        xrp_free = bal['free'].get('XRP', 0.0)
        
        # Calcul Gain/Jour
        profit_total = st.session_state.bot["profit_total"]
        gain_jour = 0.0
        if st.session_state.bot["start_time"]:
            jours = (time.time() - st.session_state.bot["start_time"]) / 86400
            gain_jour = profit_total / jours if jours > 0 else 0.0

        c1, c2 = st.columns(2)
        c1.metric("DISPO USDC", f"{usdc_free:.2f} $")
        c2.metric("DISPO XRP", f"{xrp_free:.2f} XRP")
        
        g1, g2 = st.columns(2)
        g1.metric("PROFIT TOTAL", f"+{profit_total:.4f} $")
        g2.metric("MOYENNE / JOUR", f"{gain_jour:.2f} $")
    except: st.caption("Chargement des soldes...")

show_metrics()
st.divider()

# --- 4. RÉGLAGES ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    p_achat = col1.number_input("PRIX ACHAT", value=st.session_state.bot["pa"], format="%.4f")
    p_vente = col2.number_input("PRIX VENTE", value=st.session_state.bot["pv"], format="%.4f")

# --- 5. LOGIQUE ALL-IN ---
def place_all_in_buy():
    bal = kraken.fetch_balance()
    usdc_dispo = bal['free'].get('USDC', 0.0)
    if usdc_dispo < 5: return None
    
    vol = float(kraken.amount_to_precision('XRP/USDC', usdc_dispo / st.session_state.bot["pa"]))
    res = kraken.create_limit_buy_order('XRP/USDC', vol, st.session_state.bot["pa"], {'post-only': True})
    return res['id'], vol

def place_all_in_sell(volume_reçu):
    # On utilise le volume reçu de l'achat précédent pour être sûr de tout vendre
    res = kraken.create_limit_sell_order('XRP/USDC', volume_reçu, st.session_state.bot["pv"])
    return res['id']

# --- 6. CONTRÔLE DU BOT ---
if st.session_state.bot["status"] == "OFF":
    if st.button("🚀 LANCER LE CYCLE INFINI", use_container_width=True, type="primary"):
        try:
            oid, vol = place_all_in_buy()
            st.session_state.bot.update({
                "status": "ACHAT", "pa": p_achat, "pv": p_vente, 
                "oid": oid, "last_vol": vol, "start_time": time.time()
            })
            st.rerun()
        except Exception as e: st.error(f"Erreur : {e}")
else:
    if st.button("🛑 ARRÊTER LE BOT", use_container_width=True):
        try: kraken.cancel_order(st.session_state.bot["oid"])
        except: pass
        st.session_state.bot["status"] = "OFF"
        st.rerun()

# --- 7. LE MOTEUR (FRAGMENT) ---
if st.session_state.bot["status"] != "OFF":
    @st.fragment(run_every=15)
    def engine():
        bot = st.session_state.bot
        try:
            order = kraken.fetch_order(bot["oid"], 'XRP/USDC')
            
            if order['status'] == 'closed':
                if bot["status"] == "ACHAT":
                    # L'achat est fini, on vend IMMÉDIATEMENT tout le XRP acheté
                    # On utilise order['filled'] pour vendre exactement ce qu'on a reçu
                    new_oid = place_all_in_sell(order['filled'])
                    st.session_state.bot.update({"status": "VENTE", "oid": new_oid, "last_vol": order['filled']})
                    st.toast("🎯 Achat rempli ! Placement de la vente...")
                    st.rerun()
                
                elif bot["status"] == "VENTE":
                    # La vente est finie, on recalcule le profit et on RE-ACHÈTE ALL-IN
                    st.session_state.bot["profit_total"] += (bot["pv"] - bot["pa"]) * order['filled']
                    st.session_state.bot["cycles"] += 1
                    
                    new_oid, new_vol = place_all_in_buy()
                    st.session_state.bot.update({"status": "ACHAT", "oid": new_oid, "last_vol": new_vol})
                    st.toast(f"💰 Cycle {bot['cycles']} terminé ! Relance All-In...")
                    st.rerun()
            
            st.info(f"⚡ Ordre {bot['status']} actif | Volume : {bot['last_vol']:.2f} XRP")
            st.caption(f"Sync : {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e: st.caption(f"Attente Kraken... {e}")

    engine()
