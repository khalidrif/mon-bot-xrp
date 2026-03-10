import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro Stable", layout="wide")
DB_FILE = "config_bots_xrp_stable.json"
symbol = "XRP/USDC"

# ------------------------------------------------------------
# AUTO-REFRESH 100% STREAMLIT CLOUD SAFE
# ------------------------------------------------------------
def auto_refresh():
    refresh_rate = 2000  # 2 sec
    st.markdown(f"""
        <script>
            setTimeout(function() {{
                document.getElementById('refresh_btn').click();
            }}, {refresh_rate});
        </script>
    """, unsafe_allow_html=True)

    st.button("Refresh", key="refresh_btn")

auto_refresh()

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
# RESET BOT (SUPPRESSION)
# ------------------------------------------------------------
def reset_bot(i):
    st.session_state.bots[i] = {
        "actif": False,
        "p_achat": 1.35,
        "p_vente": 1.38,
        "mise": 15.0,
        "etape": "ATTENTE_ACHAT",
        "qty": 0.0,
        "cycles": 0,
        "gain_cumule": 0.0,
    }
    save_config(st.session_state.bots)

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
# EXECUTION D’UN CYCLE
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

    st.session_state.last_price = price
    st.session_state.usdc = usdc

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

# Run cycle
run_cycle()

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("🚀 XRP Sniper Pro 50 — Version stable (sans clignotement)")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration Bot")

    id_bot = st.selectbox("Bot n°", range(1, 51))
    bot = st.session_state.bots[id_bot]

    bot["actif"] = st.toggle("Activer", value=bot["actif"])
    bot["p_achat"] = st.number_input("Prix Achat", value=bot["p_achat"], format="%.4f")
    bot["p_vente"] = st.number_input("Prix Vente", value=bot["p_vente"], format="%.4f")
    bot["mise"] = st.number_input("Mise USDC", value=bot["mise"], min_value=1.0)

    if st.button("💾 Sauvegarder"):
        save_config(st.session_state.bots)
        st.toast("Sauvegardé ✔")

    if st.button("🗑 Supprimer ce bot"):
        reset_bot(id_bot)
        st.toast(f"Bot #{id_bot} supprimé")

    st.divider()

    if st.button("🚀 Démarrer"):
        st.session_state.run = True

    if st.button("🛑 Stop"):
        st.session_state.run = False

# Metrics
price = st.session_state.get("last_price")
usdc = st.session_state.get("usdc", 0)
gain_total = sum(b["gain_cumule"] for b in st.session_state.bots.values())

c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP", f"{price:.4f}" if price else "...")
c2.metric("USDC Libre", f"{usdc:.2f}")
c3.metric("Gain Total", f"{gain_total:.4f}")

st.divider()

# Tableau bots
cols = st.columns([0.5, 1.2, 1, 1, 0.8, 0.8, 1, 0.6])
headers = ["N°", "État", "Achat", "Vente", "Mise", "Cycles", "Gain", ""]

for col, txt in zip(cols, headers):
    col.write(f"**{txt}**")

for i, bot in st.session_state.bots.items():
    if bot["actif"]:
        c = st.columns([0.5, 1.2, 1, 1, 0.8, 0.8, 1, 0.6])
        c[0].write(str(i))
        c[1].write("⏳ Achat" if bot["etape"] == "ATTENTE_ACHAT" else "💰 Vente")
        c[2].write(bot["p_achat"])
        c[3].write(bot["p_vente"])
        c[4].write(bot["mise"])
        c[5].write(bot["cycles"])
        c[6].write(round(bot["gain_cumule"], 4))

        if c[7].button("🗑", key=f"delete_{i}"):
            reset_bot(i)
            st.toast(f"Bot #{i} supprimé")
