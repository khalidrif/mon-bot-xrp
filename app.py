import streamlit as st
import ccxt
import json
import os
import time
from streamlit_autorefresh import st_autorefresh

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro Stable", layout="wide")
DB_FILE = "config_bots_xrp_stable.json"
symbol = "XRP/USDC"

# ------------------------------------------------------------
# JSON CONFIG
# ------------------------------------------------------------
def save_config(bots):
    with open(DB_FILE, "w") as f:
        json.dump(bots, f)

def load_config():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                d = json.load(f)
                return {int(k): v for k, v in d.items()}
        except:
            return None
    return None

# ------------------------------------------------------------
# INIT BOTS
# ------------------------------------------------------------
if "bots" not in st.session_state:
    saved = load_config()
    if saved:
        st.session_state.bots = saved
    else:
        st.session_state.bots = {
            i: {
                "actif": False,
                "p_achat": 1.35,
                "p_vente": 1.38,
                "mise": 15.0,
                "etape": "ATTENTE_ACHAT",
                "qty": 0.0,
                "cycles": 0,
                "gain_cumule": 0.0,
            } for i in range(1, 51)
        }

if "run" not in st.session_state:
    st.session_state.run = False

# ------------------------------------------------------------
# KRAKEN
# ------------------------------------------------------------
@st.cache_resource
def get_exchange():
    ex = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True
    })
    ex.load_markets()
    return ex

exchange = get_exchange()

# ------------------------------------------------------------
# EXECUTION D’UN CYCLE TRADING
# ------------------------------------------------------------
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
    except:
        price = None

    try:
        bal = exchange.fetch_balance()
        usdc = bal["free"].get("USDC", 0)
    except:
        usdc = 0

    st.session_state["last_price"] = price
    st.session_state["usdc"] = usdc

    if not st.session_state.run:
        return

    for i, bot in st.session_state.bots.items():

        # ACHAT
        if bot["actif"] and bot["etape"] == "ATTENTE_ACHAT":
            if price and price <= bot["p_achat"] and usdc >= bot["mise"]:
                mise_net = bot["mise"] * 0.985
                qty = float(exchange.amount_to_precision(symbol, mise_net / price))
                try:
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"] = qty
                    bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                    return
                except:
                    pass

        # VENTE
        if bot["actif"] and bot["etape"] == "ATTENTE_VENTE":
            if price and price >= bot["p_vente"] and bot["qty"] > 0:
                qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.99))
                try:
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = ((bot["p_vente"] - bot["p_achat"]) * bot["qty"]) - (bot["mise"] * 0.006)
                    bot["gain_cumule"] += gain
                    bot["qty"] = 0
                    bot["cycles"] += 1
                    bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    return
                except:
                    pass

# Lancer un cycle
run_cycle()

# ------------------------------------------------------------
# INTERFACE
# ------------------------------------------------------------
st.title("🚀 XRP Sniper Pro 50 — Version Stable (sans clignotement)")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration Bot")

    id_bot = st.selectbox("Bot n°", range(1, 51))
    bot = st.session_state.bots[id_bot]

    bot["actif"] = st.toggle("Activer", value=bot["actif"])
    bot["p_achat"] = st.number_input("Prix achat", value=bot["p_achat"], format="%.4f")
    bot["p_vente"] = st.number_input("Prix vente", value=bot["p_vente"], format="%.4f")
    bot["mise"] = st.number_input("Mise (USDC)", value=bot["mise"], min_value=1.0)

    if st.button("💾 Sauvegarder"):
        save_config(st.session_state.bots)
        st.toast("Sauvegardé ✔")

    st.divider()

    if st.button("🚀 Démarrer"):
        st.session_state.run = True

    if st.button("🛑 Stop"):
        st.session_state.run = False

# Top metrics
price = st.session_state.get("last_price")
usdc = st.session_state.get("usdc", 0)
gain_total = sum(b["gain_cumule"] for b in st.session_state.bots.values())

c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP", f"{price:.4f}" if price else "...")
c2.metric("USDC Libre", f"{usdc:.2f}")
c3.metric("Gain total", f"{gain_total:.4f}")

st.divider()

# Tableau bots
cols = st.columns([0.5, 1.5, 1, 1, 0.8, 0.8, 1])
for a, b in zip(cols, ["N°", "État", "Achat", "Vente", "Mise", "Cycles", "Gain"]):
    a.write(f"**{b}**")

for i, bot in st.session_state.bots.items():
    if bot["actif"]:
        c = st.columns([0.5, 1.5, 1, 1, 0.8, 0.8, 1])
        c[0].write(f"{i}")
        c[1].write("⏳ Achat" if bot["etape"] == "ATTENTE_ACHAT" else "💰 Vente")
        c[2].write(bot["p_achat"])
        c[3].write(bot["p_vente"])
        c[4].write(bot["mise"])
        c[5].write(bot["cycles"])
        c[6].write(round(bot["gain_cumule"], 4))

# ------------------------------------------------------------
# AUTO REFRESH FLUIDE (sans clignotement)
# ------------------------------------------------------------
st_autorefresh(interval=2000, key="refresh_stable")
