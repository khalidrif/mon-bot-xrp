import streamlit as st
import ccxt
import time

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

# --- 2. ÉTAT DU BOT ---
if 'bot' not in st.session_state:
    st.session_state.bot = {
        "status": "OFF", "pa": 1.40, "pv": 1.45, 
        "oid": None, "cycles": 0, "profit_total": 0.0, "last_vol": 0.0
    }

st.title("🏓 XRP Solo Ping-Pong")

# --- 3. AFFICHAGE DU SOLDE (DYNAMIQUE) ---
def show_balance():
    try:
        bal = kraken.fetch_balance()
        usdc_free = bal['free'].get('USDC', 0.0)
        xrp_free = bal['free'].get('XRP', 0.0)
        
        col_b1, col_b2 = st.columns(2)
        col_b1.metric("SOLDE USDC", f"{usdc_free:.2f} $")
        col_b2.metric("SOLDE XRP", f"{xrp_free:.2f} XRP")
    except:
        st.error("Impossible de récupérer les soldes.")

st.subheader("💰 Portefeuille")
show_balance()
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
                st.session_state.bot.update({"status": "ACHAT", "pa": p_achat, "pv": p_vente, "oid": res['id'], "last_vol": vol})
                st.rerun()
        except Exception as e: st.error(f"Erreur : {e}")
else:
    if st.button("🛑 ARRÊTER LE BOT", use_container_width=True):
        try: kraken.cancel_order(st.session_state.bot["oid"])
        except: pass
        st.session_state.bot["status"] = "OFF"
        st.rerun()

# --- 6. MOTEUR DE TRADING (FRAGMENT) ---
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

            # Stats en direct
            ticker = kraken.fetch_ticker('XRP/USDC')
            s1, s2, s3 = st.columns(3)
            s1.metric("PRIX XRP", f"{ticker['last']:.4f}")
            s2.metric("CYCLE ACTIF", bot["status"])
            s3.metric("PROFIT TOTAL", f"+{bot['profit_total']:.2f} $")
            st.caption(f"Dernière vérification : {time.strftime('%H:%M:%S')}")

        except Exception as e:
            st.caption(f"Attente Kraken... {e}")

    trading_engine()
