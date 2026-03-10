import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro", layout="wide")
DB_FILE = "config_bots_xrp_secure.json"
SYMBOL = "XRP/USDC"

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")
    if len(st.session_state.logs) > 15: st.session_state.logs.pop(0)

# ------------------------------------------------------------
# PERSISTENCE
# ------------------------------------------------------------
def save_config(bots):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(bots, f)
    except: pass

def load_config():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
            return {int(k): v for k, v in data.items()}
        except: return None
    return None

# ------------------------------------------------------------
# INITIALISATION
# ------------------------------------------------------------
if "bots" not in st.session_state:
    cfg = load_config()
    st.session_state.bots = cfg if cfg else {
        i: {"actif": False, "p_achat": 1.35, "p_vente": 1.38, "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "cycles": 0, "gain_cumule": 0.0}
        for i in range(1, 51)
    }

if "run" not in st.session_state:
    st.session_state.run = False

# ------------------------------------------------------------
# KRAKEN & LOGIQUE
# ------------------------------------------------------------
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })

exchange = get_exchange()

def run_cycle():
    if not exchange or not st.session_state.run: return
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        price = ticker["last"]
        bal = exchange.fetch_balance()
        st.session_state.price = price
        st.session_state.usdc = bal["free"].get("USDC", 0)
        st.session_state.xrp = bal["free"].get("XRP", 0)

        for i, bot in st.session_state.bots.items():
            if not bot["actif"]: continue

            if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                if st.session_state.usdc >= bot["mise"]:
                    qty = float(exchange.amount_to_precision(SYMBOL, (bot["mise"] * 0.98) / price))
                    exchange.create_market_buy_order(SYMBOL, qty)
                    bot.update({"qty": qty, "etape": "ATTENTE_VENTE"})
                    save_config(st.session_state.bots)
                    log(f"✅ Bot {i} acheté")

            elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                qty_sell = float(exchange.amount_to_precision(SYMBOL, bot["qty"]))
                exchange.create_market_sell_order(SYMBOL, qty_sell)
                bot["gain_cumule"] += (bot["p_vente"] - bot["p_achat"]) * bot["qty"]
                bot.update({"qty": 0, "etape": "ATTENTE_ACHAT", "cycles": bot["cycles"]+1})
                save_config(st.session_state.bots)
                log(f"💰 Bot {i} vendu")
    except Exception as e:
        log(f"Erreur: {e}")

run_cycle()

# ------------------------------------------------------------
# INTERFACE (UI)
# ------------------------------------------------------------
# INDICATEUR GLOBAL EN HAUT
is_any_active = any(b["actif"] for b in st.session_state.bots.values())
if st.session_state.run and is_any_active:
    st.markdown("### 🟢 SYSTÈME ACTIF")
else:
    st.markdown("### 🔴 SYSTÈME ARRÊTÉ")

st.title("🚀 XRP Sniper Pro")

with st.sidebar:
    st.header("⚙️ Configuration")
    id_bot = st.selectbox("Bot n°", range(1, 51))
    bot = st.session_state.bots[id_bot]
    
    bot["actif"] = st.toggle("Activer ce bot", bot["actif"])
    bot["p_achat"] = st.number_input("Prix Achat", value=bot["p_achat"], format="%.4f")
    bot["p_vente"] = st.number_input("Prix Vente", value=bot["p_vente"], format="%.4f")
    bot["mise"] = st.number_input("Mise ($)", value=bot["mise"])
    
    if st.button("💾 Sauvegarder"):
        save_config(st.session_state.bots)
        st.toast("Enregistré")

    st.divider()
    if st.button("▶️ DÉMARRER", use_container_width=True):
        st.session_state.run = True
        st.rerun()
    if st.button("🛑 STOP", type="primary", use_container_width=True):
        st.session_state.run = False
        st.rerun()

# DASHBOARD
p = st.session_state.get("price", 0)
u = st.session_state.get("usdc", 0)
g = sum(b["gain_cumule"] for b in st.session_state.bots.values())

c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP", f"{p:.4f} $")
c2.metric("Solde USDC", f"{u:.2f} $")
c3.metric("Profit Total", f"{g:.2f} $")

st.divider()

# RÉSUMÉ COMPACT DES BOTS ACTIFS
st.subheader("Bots en cours")
active_list = [f"Bot #{i} ({b['etape']})" for i, b in st.session_state.bots.items() if b["actif"]]
if active_list:
    st.write(", ".join(active_list))
else:
    st.write("Aucun bot actif.")

with st.expander("Logs"):
    for l in reversed(st.session_state.logs):
        st.text(l)

time.sleep(2)
st.rerun()
