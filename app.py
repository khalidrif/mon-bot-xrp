
import streamlit as st
import ccxt
from streamlit_autorefresh import st_autorefresh

# ---------------------------
# CONFIG APP
# ---------------------------
st.set_page_config(page_title="Kraken Multi-Bots XRP", page_icon="🤖", layout="wide")

# Style iPhone + couleurs bots
st.markdown("""
<style>
@media (max-width: 600px) {
    .block-container {
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
}
.status-green {
    background:#1FAA59;color:white;padding:6px 12px;border-radius:6px;
}
.status-red {
    background:#B4161B;color:white;padding:6px 12px;border-radius:6px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# CONNEXION KRAKEN
# ---------------------------
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True,
    })
except Exception:
    st.error("Erreur clé API")
    st.stop()

# Refresh auto 10 sec
st_autorefresh(interval=10000, key="refresh_loop")

# ---------------------------
# SESSION STATE
# ---------------------------
if "auto_bot_status" not in st.session_state:
    st.session_state.auto_bot_status = "VEILLE"

if "manual_bots" not in st.session_state:
    st.session_state.manual_bots = {
        f"bot{i}": {
            "enabled": False,
            "status": "VEILLE",
            "buy": 0.0,
            "sell": 0.0,
            "entry_price": None,
            "gain": 0.0,
        }
        for i in range(1, 4)   # 3 bots manuels
    }

# ---------------------------
# DONNÉES KRANKEN
# ---------------------------
try:
    ticker = exchange.fetch_ticker("XRP/USD")
    prix = ticker["last"]

    balance = exchange.fetch_balance()

    usd = 0.0
    for s in ["USDC", "USD", "ZUSD"]:
        if s in balance["total"]:
            usd = balance["total"][s]
            break

    xrp = balance["total"].get("XRP", 0.0)

except Exception as e:
    st.error(f"Erreur Kraken : {e}")
    st.stop()

# ---------------------------
# BARRE LATERALE
# ---------------------------
st.sidebar.title("🤖 Multi-Bots")

for i in range(1, 4):
    b = st.session_state.manual_bots[f"bot{i}"]
    color = "#1FAA59" if b["enabled"] else "#B4161B"

    st.sidebar.markdown(
        f"<div style='color:{color};font-weight:bold;'>● Bot {i} — {b['status']}</div>",
        unsafe_allow_html=True
    )

    if st.sidebar.button(f"{'Désactiver' if b['enabled'] else 'Activer'} Bot {i}"):
        b["enabled"] = not b["enabled"]
        b["status"] = "ATTENTE_ACHAT" if b["enabled"] else "VEILLE"
        st.rerun()

    st.sidebar.metric(f"Gain Bot {i}", f"{round(b['gain'],4)} $")
    st.sidebar.write("")

# ---------------------------
# DASHBOARD
# ---------------------------
st.title("🤖 Multi-Bots XRP Kraken")

c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP", f"{prix:.4f} $")
c2.metric("USD", f"{round(usd,2)} $")
c3.metric("XRP", f"{round(xrp,4)}")

# ---------------------------
# PARAMÈTRES DES 3 BOTS
# ---------------------------
st.subheader("⚙️ Paramétrage des Bots Manuels")

for i in range(1, 4):
    b = st.session_state.manual_bots[f"bot{i}"]

    st.markdown(f"### Bot {i}")

    colA, colB = st.columns(2)
    b["buy"] = colA.number_input(
        f"Bot {i} — Acheter si prix ≤",
        value=float(prix * 0.99),
        format="%.4f",
        key=f"buy_{i}"
    )
    b["sell"] = colB.number_input(
        f"Bot {i} — Vendre si prix ≥",
        value=float(prix * 1.01),
        format="%.4f",
        key=f"sell_{i}"
    )

    if b["enabled"]:
        color = "#1FAA59" if b["status"] == "EN_POSITION" else "#B4161B"
        st.markdown(
            f"<div style='background:{color};padding:10px;border-radius:6px;color:white;text-align:center;'>"
            f"Achat ≤ {b['buy']} | Vente ≥ {b['sell']}"
            f"</div>",
            unsafe_allow_html=True
        )

# ---------------------------
# LOGIQUE DES 3 BOTS
# ---------------------------
for i in range(1, 4):
    b = st.session_state.manual_bots[f"bot{i}"]

    if not b["enabled"]:
        continue

    # Achat
    if b["status"] == "ATTENTE_ACHAT":
        if prix <= b["buy"] and usd > 5:
            qty = (usd - 1) / prix
            exchange.create_market_buy_order("XRP/USD", qty)
            b["entry_price"] = prix
            b["status"] = "EN_POSITION"
            st.success(f"Bot {i}: ACHAT {qty:.2f} XRP")
            st.rerun()

    # Vente
    if b["status"] == "EN_POSITION":
        if prix >= b["sell"] and xrp > 1:
            exchange.create_market_sell_order("XRP/USD", xrp)
            gain = (prix - b["entry_price"]) * xrp
            b["gain"] += gain
            b["status"] = "ATTENTE_ACHAT"
            st.success(f"Bot {i}: VENTE +{gain:.4f} $")
            st.rerun()

# ---------------------------
# STOP GENERAL
# ---------------------------
if st.button("🛑 STOP TOUS LES BOTS"):
    for i in range(1, 4):
        b = st.session_state.manual_bots[f"bot{i}"]
        b["enabled"] = False
        b["status"] = "VEILLE"
    st.rerun()
