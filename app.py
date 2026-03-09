import streamlit as st
import ccxt
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP 50 Bots Solo", layout="wide")

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
if 'bots_data' not in st.session_state:
    # On initialise 50 structures de données indépendantes
    st.session_state.bots_data = {}
    for i in range(1, 51):
        st.session_state.bots_data[i] = {
            "p_achat": 1.3500 - (i * 0.001),
            "p_vente": 1.3800,
            "mise": 10.0,
            "etape": "ATTENTE_ACHAT",
            "actif": False
        }

if 'global_run' not in st.session_state:
    st.session_state.global_run = False

# --- INTERFACE PRINCIPALE ---
st.title("🤖 50 Bots XRP Indépendants")

# Récupération Prix & Balances
try:
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['last']
    time.sleep(0.5)
    bal = exchange.fetch_balance()
    usdc_bal = bal['free'].get('USDC', 0.0)
    xrp_bal = bal['free'].get('XRP', 0.0)
    
    col_p, col_b = st.columns(2)
    col_p.metric("Prix XRP Actuel", f"{price:.4f} USDC")
    col_b.write(f"💰 Portefeuille : **{usdc_bal:.2f} USDC** | **{xrp_bal:.2f} XRP**")
except Exception as e:
    st.error(f"Erreur API : {e}")
    st.stop()

st.divider()

# Contrôles Généraux
c1, c2, c3 = st.columns(3)
if c1.button("🚀 LANCER TOUS LES BOTS ACTIFS", type="primary", use_container_width=True):
    st.session_state.global_run = True
if c2.button("🛑 STOP TOUT", use_container_width=True):
    st.session_state.global_run = False
if c3.button("🔄 Reset tous les états à ACHAT"):
    for i in range(1, 51): st.session_state.bots_data[i]["etape"] = "ATTENTE_ACHAT"
    st.rerun()

st.divider()

# --- RÉGLAGE INDIVIDUEL (Une par une) ---
st.subheader("⚙️ Configuration des Paliers")
cols = st.columns(2) # On affiche sur 2 colonnes pour gagner de la place

for i in range(1, 51):
    with (cols[0] if i <= 25 else cols[1]):
        with st.expander(f"🤖 BOT N°{i} - {st.session_state.bots_data[i]['etape']}", expanded=False):
            # Saisie Manuelle
            st.session_state.bots_data[i]["actif"] = st.checkbox("Activer ce bot", value=st.session_state.bots_data[i]["actif"], key=f"on_{i}")
            st.session_state.bots_data[i]["p_achat"] = st.number_input(f"Prix ACHAT Bot {i}", value=st.session_state.bots_data[i]["p_achat"], format="%.4f", key=f"ac_{i}")
            st.session_state.bots_data[i]["p_vente"] = st.number_input(f"Prix VENTE Bot {i}", value=st.session_state.bots_data[i]["p_vente"], format="%.4f", key=f"ve_{i}")
            st.session_state.bots_data[i]["mise"] = st.number_input(f"Mise USDC Bot {i}", value=st.session_state.bots_data[i]["mise"], key=f"mi_{i}")

# --- LOGIQUE DE TRADING ---
if st.session_state.global_run:
    for i in range(1, 51):
        bot = st.session_state.bots_data[i]
        if bot["actif"]:
            # LOGIQUE ACHAT
            if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                if usdc_bal >= bot["mise"]:
                    st.warning(f"⚡ BOT {i} : Achat à {bot['p_achat']}...")
                    q = float(exchange.amount_to_precision(symbol, bot["mise"] / bot["p_achat"]))
                    p = float(exchange.price_to_precision(symbol, bot["p_achat"]))
                    
                    exchange.create_limit_buy_order(symbol, q, p)
                    bot["etape"] = "ATTENTE_VENTE"
                    st.rerun()

            # LOGIQUE VENTE
            elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                # Calcul de la quantité à revendre (basé sur l'achat initial)
                st.info(f"💰 BOT {i} : Vente à {bot['p_vente']}...")
                q_v = float(exchange.amount_to_precision(symbol, (bot["mise"] / bot["p_achat"]) * 0.995))
                p_v = float(exchange.price_to_precision(symbol, bot["p_vente"]))
                
                exchange.create_limit_sell_order(symbol, q_v, p_v)
                bot["etape"] = "ATTENTE_ACHAT"
                st.balloons()
                st.rerun()

    time.sleep(20)
    st.rerun()
