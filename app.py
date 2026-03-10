import streamlit as st
import ccxt
import asyncio
import json
import os
import time
import threading
import streamlit.components.v1 as components

# ------------------------------------------------------------
# CONFIG PAGE
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro Async", layout="wide")
DB_FILE = "config_bots_xrp_async.json"
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
                "last_trigger": 0
            } for i in range(1, 51)
        }

if "run" not in st.session_state:
    st.session_state.run = False

if "ticker_price" not in st.session_state:
    st.session_state.ticker_price = None

if "async_started" not in st.session_state:
    st.session_state.async_started = False


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
# ASYNC LOOP PRICE
# ------------------------------------------------------------
async def fetch_price_loop():
    while True:
        try:
            ticker = exchange.fetch_ticker(symbol)
            st.session_state.ticker_price = ticker["last"]
        except:
            st.session_state.ticker_price = None
        await asyncio.sleep(1)


# ------------------------------------------------------------
# ASYNC BOT LOOP
# ------------------------------------------------------------
async def bot_loop(bot_id):
    while True:
        bot = st.session_state.bots[bot_id]

        if not st.session_state.run:
            await asyncio.sleep(1)
            continue

        price = st.session_state.ticker_price
        if price is None:
            await asyncio.sleep(0.1)
            continue

        now = time.time()
        if now - bot["last_trigger"] < 1:
            await asyncio.sleep(0.05)
            continue

        # -------------- ACHAT --------------
        if bot["actif"] and bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:

            bal = exchange.fetch_balance()
            usdc = bal["free"].get("USDC", 0)

            if usdc >= bot["mise"]:
                mise_net = bot["mise"] * 0.985
                qty = float(exchange.amount_to_precision(symbol, mise_net / price))

                try:
                    exchange.create_market_buy_order(symbol, qty)

                    bot["qty"] = qty
                    bot["etape"] = "ATTENTE_VENTE"
                    bot["last_trigger"] = now

                    save_config(st.session_state.bots)

                except:
                    pass

        # -------------- VENTE --------------
        if bot["actif"] and bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:

            qty = bot["qty"]

            if qty > 0:
                qty_sell = float(exchange.amount_to_precision(symbol, qty * 0.99))

                try:
                    exchange.create_market_sell_order(symbol, qty_sell)

                    gain_net = ((bot["p_vente"] - bot["p_achat"]) * qty) - (bot["mise"] * 0.006)

                    bot["gain_cumule"] += gain_net
                    bot["cycles"] += 1
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    bot["last_trigger"] = now

                    save_config(st.session_state.bots)

                except:
                    pass

        await asyncio.sleep(0.05)


# ------------------------------------------------------------
# ASYNC STARTER (THREAD)
# ------------------------------------------------------------
async def main_async():
    await asyncio.gather(
        fetch_price_loop(),
        *(bot_loop(i) for i in st.session_state.bots.keys())
    )


def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_async())


if not st.session_state.async_started:
    st.session_state.async_started = True
    threading.Thread(target=start_async_loop, daemon=True).start()


# ------------------------------------------------------------
# UI STREAMLIT
# ------------------------------------------------------------
st.title("🚀 XRP Sniper Pro 50 — Version Async")


# ---------------- Sidebar -----------------
with st.sidebar:
    st.header("⚙️ Configuration Bot")

    id_bot = st.selectbox("Bot n°", range(1, 51))
    bot = st.session_state.bots[id_bot]

    bot["actif"] = st.toggle("Activer", value=bot["actif"])
    bot["p_achat"] = st.number_input("Prix achat", value=bot["p_achat"], format="%.4f")
    bot["p_vente"] = st.number_input("Prix vente", value=bot["p_vente"], format="%.4f")
    bot["mise"] = st.number_input("Mise USDC", value=bot["mise"], min_value=1.0)

    if st.button("💾 Sauvegarder"):
        save_config(st.session_state.bots)
        st.toast("Configuration enregistrée")

    st.divider()

    if st.button("🚀 Démarrer"):
        st.session_state.run = True

    if st.button("🛑 Stop"):
        st.session_state.run = False


# ---------------- Dashboard -----------------
price = st.session_state.ticker_price

try:
    bal = exchange.fetch_balance()
    usdc = bal["free"].get("USDC", 0)
except:
    usdc = 0

gain_total = sum(b["gain_cumule"] for b in st.session_state.bots.values())

c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP", f"{price:.4f}" if price else "...")
c2.metric("USDC libre", f"{usdc:.2f}")
c3.metric("Gain total", f"{gain_total:.4f}")

st.divider()


# ---------------- Tableau BOTS -----------------
cols = st.columns([0.5, 1.2, 1, 1, 0.8, 0.8, 1])
headers = ["N°", "État", "Achat", "Vente", "Mise", "Cycles", "Gain"]

for i, h in enumerate(headers):
    cols[i].write(f"**{h}**")

for i, bot in st.session_state.bots.items():
    if bot["actif"]:
        c = st.columns([0.5, 1.2, 1, 1, 0.8, 0.8, 1])

        c[0].write(f"#{i}")
        c[1].write("⏳ ACHAT" if bot["etape"] == "ATTENTE_ACHAT" else "💰 VENTE")
        c[2].write(f"{bot['p_achat']:.4f}")
        c[3].write(f"{bot['p_vente']:.4f}")
        c[4].write(f"{bot['mise']}$")
        c[5].write(bot["cycles"])
        c[6].write(f"{bot['gain_cumule']:.4f}$")


# ------------------------------------------------------------
# 🔁 AUTO-REFRESH PROPRE (1 seconde)
# ------------------------------------------------------------
components.html("""
    <script>
        setTimeout(function() { window.location.reload(); }, 1000);
    </script>
""", height=0)
