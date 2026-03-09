import streamlit as st
import ccxt
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP 50 Bots Frames", layout="wide")

@st.cache_resource
def get_exchange():
    ex = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': 'milliseconds'}
    })
    ex.load_markets()
    return ex

exchange = get_exchange()
symbol = "XRP/USDC"

# --- MÉMOIRE DES 50 BOTS ---
if 'bots' not in st.session_state:
    st.session_state.bots = {}
    for i in range(1, 51):
        st.session_state.bots[i] = {
            "p_achat": 1.3500 - (i * 0.002),
            "p_vente": 1.3800,
            "mise": 10.0,
            "etape": "ATTENTE_ACHAT",
            "actif": False
        }

if 'run' not in st.session_state: st.session_state.run = False

# --- BARRE LATÉRALE (SAISIE GAUCHE) ---
with st.sidebar:
    st.header("⚙️ Configuration des 50 Bots")
    st.info("Réglez chaque bot un par un ici.")
    
    # Menu déroulant pour choisir quel bot configurer (pour éviter une sidebar de 10km)
    choix_bot = st.selectbox("Sélectionner un Bot à régler", range(1, 51))
    
    with st.container(border=True):
        st.subheader(f"Réglage Bot n°{choix_bot}")
        st.session_state.bots[choix_bot]["actif"] = st.toggle("Activer ce bot", value=st.session_state.bots[choix_bot]["actif"], key=f"tgl_{choix_bot}")
        st.session_state.bots[choix_bot]["p_achat"] = st.number_input("Prix ACHAT", value=st.session_state.bots[choix_bot]["p_achat"], format="%.4f", key=f"ac_{choix_bot}")
        st.session_state.bots[choix_bot]["p_vente"] = st.number_input("Prix VENTE", value=st.session_state.bots[choix_bot]["p_vente"], format="%.4f", key=f"ve_{choix_bot}")
        st.session_state.bots[choix_bot]["mise"] = st.number_input("Mise USDC", value=st.session_state.bots[choix_bot]["mise"], key=f"mi_{choix_bot}")

    st.divider()
    if st.button("🚀 DÉMARRER TOUT", type="primary", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False
    if st.button("🔄 Reset États (Achat)"):
        for i in range(1, 51): st.session_state.bots[i]["etape"] = "ATTENTE_ACHAT"
        st.rerun()

# --- ZONE CENTRALE (AFFICHAGE DES BOTS) ---
st.title("🛰️ Dashboard Multi-Bots XRP")

# Récupération données Marché
try:
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['last']
    time.sleep(0.5)
    bal = exchange.fetch_balance()
    usdc_bal = bal['free'].get('USDC', 0.0)
    
    col_p, col_b = st.columns(2)
    col_p.metric("Prix XRP Actuel", f"{price:.4f} USDC")
    col_b.metric("Solde USDC Disponible", f"{usdc_bal:.2f}")
except Exception as e:
    st.error(f"Erreur API : {e}")
    st.stop()

st.divider()

# Affichage des bots actifs sous forme de lignes (Frame)
st.subheader("🤖 Suivi des Bots Actifs")
header_cols = st.columns([1, 2, 2, 2, 2, 1])
header_cols[0].write("**N°**")
header_cols[1].write("**État**")
header_cols[2].write("**Cible Achat**")
header_cols[3].write("**Cible Vente**")
header_cols[4].write("**Mise**")
header_cols[5].write("**Statut**")

for i in range(1, 51):
    bot = st.session_state.bots[i]
    if bot["actif"]:
        with st.container(border=True):
            cols = st.columns([1, 2, 2, 2, 2, 1])
            cols[0].write(f"#{i}")
            
            # État visuel
            if bot["etape"] == "ATTENTE_ACHAT":
                cols[1].warning("⏳ ACHAT")
            else:
                cols[1].success("💰 VENTE")
                
            cols[2].write(f"{bot['p_achat']:.4f}")
            cols[3].write(f"{bot['p_vente']:.4f}")
            cols[4].write(f"{bot['mise']} $")
            
            # Animation si le prix est proche
            proche = "🎯" if (bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]*1.01) else ""
            cols[5].write(proche)

# --- LOGIQUE DE TRADING ---
if st.session_state.run:
    for i in range(1, 51):
        bot = st.session_state.bots[i]
        if bot["actif"]:
            # ACHAT
            if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                if usdc_bal >= bot["mise"]:
                    q = float(exchange.amount_to_precision(symbol, bot["mise"] / bot["p_achat"]))
                    p = float(exchange.price_to_precision(symbol, bot["p_achat"]))
                    exchange.create_limit_buy_order(symbol, q, p)
                    bot["etape"] = "ATTENTE_VENTE"
                    st.rerun()
            # VENTE
            elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                q_v = float(exchange.amount_to_precision(symbol, (bot["mise"] / bot["p_achat"]) * 0.995))
                p_v = float(exchange.price_to_precision(symbol, bot["p_vente"]))
                exchange.create_limit_sell_order(symbol, q_v, p_v)
                bot["etape"] = "ATTENTE_ACHAT"
                st.balloons()
                st.rerun()

    time.sleep(20)
    st.rerun()
