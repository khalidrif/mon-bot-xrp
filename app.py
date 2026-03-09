import streamlit as st
import ccxt
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP 50 Grilles Manuelles", layout="wide")

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
    # On crée 50 bots avec des valeurs par défaut
    st.session_state.bots = [
        {"id": i, "p_achat": 1.3500 - (i * 0.005), "p_vente": 1.3800, "etape": "ATTENTE_ACHAT", "actif": False}
        for i in range(1, 51)
    ]

# --- INTERFACE DE RÉGLAGE ---
st.title("🤖 XRP Multi-Bot (50 Grilles Manuelles)")

with st.expander("⚙️ RÉGLER LES 50 BOTS (Prix Manuels)"):
    for i in range(50):
        c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
        bot = st.session_state.bots[i]
        c1.write(f"Bot {i+1}")
        bot["p_achat"] = c2.number_input(f"Achat {i+1}", value=bot["p_achat"], format="%.4f", key=f"ac_{i}")
        bot["p_vente"] = c3.number_input(f"Vente {i+1}", value=bot["p_vente"], format="%.4f", key=f"ve_{i}")
        bot["actif"] = c4.checkbox("Activer", value=bot["actif"], key=f"on_{i}")

# --- RÉCUPÉRATION PRIX & SOLDE ---
try:
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['last']
    time.sleep(0.5)
    bal = exchange.fetch_balance()
    usdc_bal = bal['free'].get('USDC', 0.0)
    xrp_bal = bal['free'].get('XRP', 0.0)
    
    st.metric("Prix XRP Actuel", f"{price:.4f} USDC")
    st.write(f"💰 Portefeuille : **{usdc_bal:.2f} USDC** | **{xrp_bal:.2f} XRP**")
except Exception as e:
    st.error(f"Erreur API : {e}")
    st.stop()

# --- LOGIQUE DE TRADING ---
st.divider()
st.subheader("🛰️ État des ordres en direct")

# On boucle sur les 50 bots
for bot in st.session_state.bots:
    if bot["actif"]:
        # 1. LOGIQUE ACHAT
        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            if usdc_bal >= 10.0: # Mise fixe de 10 USDC par bot pour l'exemple
                st.warning(f"⚡ Bot {bot['id']} : Achat à {bot['p_achat']}")
                q = float(exchange.amount_to_precision(symbol, 10.0 / bot["p_achat"]))
                exchange.create_limit_buy_order(symbol, q, bot["p_achat"])
                bot["etape"] = "ATTENTE_VENTE"
                st.rerun()

        # 2. LOGIQUE VENTE
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            # On vérifie si on a du XRP à vendre (approximatif par bot)
            st.info(f"💰 Bot {bot['id']} : Vente à {bot['p_vente']}")
            # Ici on vend une quantité fixe ou le stock du bot
            q_v = float(exchange.amount_to_precision(symbol, (10.0 / bot["p_achat"]) * 0.995))
            exchange.create_limit_sell_order(symbol, q_v, bot["p_vente"])
            bot["etape"] = "ATTENTE_ACHAT"
            st.rerun()

        # Affichage du statut de chaque bot actif
        st.write(f"🤖 Bot {bot['id']} | {bot['etape']} | Cible: {bot['p_achat'] if bot['etape']=='ATTENTE_ACHAT' else bot['p_vente']}")

time.sleep(20)
st.rerun()
