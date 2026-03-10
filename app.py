import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro DEBUG", layout="wide")
DB_FILE = "config_bots_xrp_debug.json"
symbol = "XRP/USDC"

# ZONE LOGS (stockée en session)
if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')}  |  {msg}")

# ------------------------------------------------------------
# AUTO-REFRESH CLOUD SAFE (NO BLINK)
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
# RESET BOT
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
    log(f"Bot #{i} réinitialisé")

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
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True
    })

exchange = get_exchange()

# ------------------------------------------------------------
# RUN CYCLE (DEBUG COMPLET)
# ------------------------------------------------------------
def run_cycle():
    # TICKER
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
        log(f"Prix XRP reçu : {price}")
    except Exception as e:
        price = None
        log(f"[ERREUR TICKER] {e}")

    # BALANCES
    try:
        bal = exchange.fetch_balance()
        usdc = bal["free"].get("USDC", 0)
        xrp = bal["free"].get("XRP", 0)
        log(f"USDC réel : {usdc}  |  XRP réel : {xrp}")
    except Exception as e:
        usdc = 0
        xrp = 0
        log(f"[ERREUR BALANCE] {e}")

    st.session_state.last_price = price
    st.session_state.usdc = usdc
    st.session_state.xrp = xrp

    if not st.session_state.run:
        log("Bots arrêtés")
        return

    # BOUCLE DES 50 BOTS
    for i, bot in st.session_state.bots.items():
        if not bot["actif"]:
            continue

        log(f"[Bot {i}]  État : {bot['etape']}  | Achat={bot['p_achat']} Vente={bot['p_vente']} Mise={bot['mise']}")

        # ---------------- ACHAT ----------------
        if bot["etape"] == "ATTENTE_ACHAT":
            if price and price <= bot["p_achat"]:
                if usdc >= bot["mise"]:
                    mise_net = bot["mise"] * 0.985
                    qty = float(exchange.amount_to_precision(symbol, mise_net / price))
                    try:
                        exchange.create_market_buy_order(symbol, qty)
                        bot["qty"] = qty
                        bot["etape"] = "ATTENTE_VENTE"
                        save_config(st.session_state.bots)
                        log(f"[Bot {i}] ACHAT OK — qty={qty}")
                        continue
                    except Exception as e:
                        log(f"[Bot {i}] ERREUR ACHAT : {e}")
                        continue
                else:
                    log(f"[Bot {i}] PAS ASSEZ DE USDC ({usdc} < {bot['mise']})")

        # ---------------- VENTE ----------------
        if bot["etape"] == "ATTENTE_VENTE":
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
                    log(f"[Bot {i}] VENTE OK — gain={gain}")
                    continue
                except Exception as e:
                    log(f"[Bot {i}] ERREUR VENTE : {e}")
                    continue

# RUN CYCLE
run_cycle()

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("🧪 XRP Sniper Pro — MODE DEBUG COMPLET")

# SIDEBAR
with st.sidebar:
    st.header("⚙️ BOT")

    id_bot = st.selectbox("Bot n°", range(1, 51))
    bot = st.session_state.bots[id_bot]

    bot["actif"] = st.toggle("Activer Bot", value=bot["actif"])
    bot["p_achat"] = st.number_input("Prix Achat", value=bot["p_achat"], format="%.4f")
    bot["p_vente"] = st.number_input("Prix Vente", value=bot["p_vente"], format="%.4f")
    bot["mise"] = st.number_input("Mise", value=bot["mise"])

    if st.button("💾 Sauvegarder"):
        save_config(st.session_state.bots)
        st.toast("Sauvegardé")

    if st.button("🗑 Supprimer ce bot"):
        reset_bot(id_bot)

    st.divider()

    if st.button("🚀 Démarrer"):
        st.session_state.run = True
        log("Démarrage bots")

    if st.button("🛑 Stop"):
        st.session_state.run = False
        log("Arrêt bots")

# METRICS
price = st.session_state.get("last_price")
usdc = st.session_state.get("usdc", 0)
xrp = st.session_state.get("xrp", 0)
gain_total = sum(b["gain_cumule"] for b in st.session_state.bots.values())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Prix XRP", f"{price:.4f}" if price else "...")
c2.metric("USDC", f"{usdc:.2f}")
c3.metric("XRP", f"{xrp:.4f}")
c4.metric("Gain Total", f"{gain_total:.4f}")

st.divider()

# TABLE BOTS
cols = st.columns([0.4, 1.2, 1, 1, 0.8, 0.8, 1])
headers = ["N°", "État", "Achat", "Vente", "Mise", "Cycles", "Gain"]

for col, txt in zip(cols, headers):
    col.write(f"**{txt}**")

for i, bot in st.session_state.bots.items():
    if bot["actif"]:
        c = st.columns([0.4, 1.2, 1, 1, 0.8, 0.8, 1])
        c[0].write(str(i))
        c[1].write(bot["etape"])
        c[2].write(bot["p_achat"])
        c[3].write(bot["p_vente"])
        c[4].write(bot["mise"])
        c[5].write(bot["cycles"])
        c[6].write(round(bot["gain_cumule"], 4))

# ------------------------------------------------------------
# LOG PANEL
# ------------------------------------------------------------
st.subheader("📝 LOGS EN DIRECT")
for line in st.session_state.logs[-30:]:
    st.write(line)
