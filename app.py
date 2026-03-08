import streamlit as st
import ccxt
from streamlit_autorefresh import st_autorefresh

# --- CONFIG GLOBAL ---
st.set_page_config(
    page_title="Kraken XRP Snowball REAL",
    page_icon="🐙",
    layout="wide",
)

# --- STYLE RESPONSIVE IPHONE ---
st.markdown("""
    <style>
    @media (max-width: 600px) {
        .block-container {
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
    }
    .status-green {
        background-color: #1FAA59;
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    .status-red {
        background-color: #B4161B;
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONNEXION KRAKEN ---
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })
except Exception:
    st.error("⚠️ Erreur : Clés API Kraken manquantes.")
    st.stop()

# --- REFRESH AUTO ---
st_autorefresh(interval=10000, key="refresh_loop")

# --- SESSION STATE ---
defaults = {
    "bot_status": "VEILLE",    # VEILLE • ATTENTE_ACHAT • EN_POSITION
    "targets": {"buy": 0.0, "sell": 0.0},
    "entry_price": None,
    "gain_total": 0.0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- RÉCUPÉRATION DES DONNÉES ---
try:
    ticker = exchange.fetch_ticker('XRP/USD')
    prix_actuel = ticker["last"]

    balance = exchange.fetch_balance()
    solde_usd = next(
        (balance["total"][s] for s in ["USDC", "USD", "ZUSD"] if s in balance["total"]),
        0.0
    )
    solde_xrp = balance["total"].get("XRP", 0.0)

except Exception as e:
    st.error(f"Erreur Kraken : {e}")
    st.stop()

# --- BARRE LATÉRALE ---
st.sidebar.title("⚙️ Contrôles du Bot")

# Pastille d'état
if st.session_state.bot_status in ["ATTENTE_ACHAT", "EN_POSITION"]:
    st.sidebar.markdown('<div class="status-green">Bot : ACTIF</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="status-red">Bot : ARRÊTÉ</div>', unsafe_allow_html=True)

st.sidebar.write(" ")

# GAIN NET
if st.session_state.entry_price:
    gain_pct = ((prix_actuel - st.session_state.entry_price) / st.session_state.entry_price) * 100
else:
    gain_pct = 0

st.sidebar.metric("Gain Net", f"{round(st.session_state.gain_total, 4)} $")
st.sidebar.metric("Gain Trade en cours", f"{gain_pct:.2f} %")

# Contrôles manuels
st.sidebar.subheader("🖐 Mode manuel")

if st.sidebar.button("Acheter XRP (market)"):
    if solde_usd > 5:
        qty = (solde_usd - 1) / prix_actuel
        exchange.create_market_buy_order("XRP/USD", qty)
        st.success(f"Achat manuel fait : {qty:.2f} XRP")
        st.rerun()

if st.sidebar.button("Vendre XRP (market)"):
    if solde_xrp > 1:
        exchange.create_market_sell_order("XRP/USD", solde_xrp)
        st.success(f"Vente manuelle faite : {solde_xrp:.2f} XRP")
        st.rerun()

# --- DASHBOARD ---
st.title("🐙 Kraken XRP Auto-Snowball")

c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP", f"{prix_actuel:.4f} $")
c2.metric("USD Disponible", f"{round(solde_usd, 2)} $")
c3.metric("XRP Disponible", f"{round(solde_xrp, 4)}")

# --- FOURCHETTE DE PRIX COLORÉE ---
if st.session_state.bot_status == "ATTENTE_ACHAT":
    color = "#B4161B"  # rouge
else:
    color = "#1FAA59"  # vert

st.markdown(
    f"""
    <div style='padding:10px;border-radius:8px;background:{color};color:white;font-weight:bold;text-align:center;'>
        Fourchette prix : Achat ≤ {st.session_state.targets["buy"]}  |  Vente ≥ {st.session_state.targets["sell"]}
    </div>
    """,
    unsafe_allow_html=True
)

# --- CONFIGURATION ---
with st.container():
    st.subheader("❄️ Paramètres du Bot")

    col1, col2 = st.columns(2)
    buy = col1.number_input("Acheter si prix ≤", value=float(prix_actuel * 0.99), format="%.4f")
    sell = col2.number_input("Vendre si prix ≥", value=float(prix_actuel * 1.01), format="%.4f")

    if st.button("🚀 Activer Bot"):
        st.session_state.targets["buy"] = buy
        st.session_state.targets["sell"] = sell
        st.session_state.bot_status = "ATTENTE_ACHAT"
        st.session_state.entry_price = None
        st.rerun()

# --- LOGIQUE BOT ---
try:
    # Achat
    if st.session_state.bot_status == "ATTENTE_ACHAT":
        if prix_actuel <= st.session_state.targets["buy"] and solde_usd > 5:
            qty = (solde_usd - 1) / prix_actuel
            exchange.create_market_buy_order("XRP/USD", qty)

            st.session_state.entry_price = prix_actuel
            st.session_state.bot_status = "EN_POSITION"

            st.success(f"ACHAT AUTO : {qty:.2f} XRP")
            st.rerun()

    # Vente
    if st.session_state.bot_status == "EN_POSITION":
        if prix_actuel >= st.session_state.targets["sell"] and solde_xrp > 1:
            exchange.create_market_sell_order("XRP/USD", solde_xrp)

            gain = (prix_actuel - st.session_state.entry_price) * solde_xrp
            st.session_state.gain_total += gain

            st.success(f"VENTE AUTO : +{gain:.4f} $")
            st.session_state.bot_status = "VEILLE"

            st.balloons()
            st.rerun()

except Exception as e:
    st.error(f"Erreur trading : {e}")

# --- STOP BOUTON ---
if st.button("🛑 STOP BOT"):
    st.session_state.bot_status = "VEILLE"
    st.session_state.entry_price = None
    st.session_state.targets = {"buy": 0, "sell": 0}
    st.rerun()
