import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro", layout="wide")
DB_FILE = "config_bots_xrp_secure.json"
symbol = "XRP/USDC"

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")
    if len(st.session_state.logs) > 20: st.session_state.logs.pop(0)

# ------------------------------------------------------------
# AUTO-REFRESH (FIXÉ À 1 SECONDE)
# ------------------------------------------------------------
def auto_refresh():
    st.markdown("""
        <script>
            setTimeout(function() {
                document.getElementById('refresh_button').click();
            }, 1000);
        </script>
    """, unsafe_allow_html=True)
    st.button("refresh", key="refresh_button")

auto_refresh()

# ------------------------------------------------------------
# JSON CONFIG
# ------------------------------------------------------------
def save_config(bots):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(bots, f)
    except Exception as e:
        st.error(f"❌ ERREUR SAUVEGARDE : {e}")

def load_config():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
            return {int(k): v for k, v in data.items()}
        except:
            return None
    return None

def reset_bot(i):
    st.session_state.bots[i] = {
        "actif": False, "p_achat": 1.35, "p_vente": 1.38, "mise": 15.0,
        "etape": "ATTENTE_ACHAT", "qty": 0.0, "cycles": 0, "gain_cumule": 0.0,
    }
    save_config(st.session_state.bots)

# ------------------------------------------------------------
# INIT BOTS
# ------------------------------------------------------------
if "bots" not in st.session_state:
    cfg = load_config()
    if cfg:
        st.session_state.bots = cfg
    else:
        st.session_state.bots = {
            i: {"actif": False, "p_achat": 1.35, "p_vente": 1.38, "mise": 15.0, 
                "etape": "ATTENTE_ACHAT", "qty": 0.0, "cycles": 0, "gain_cumule": 0.0}
            for i in range(1, 51)
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
        "enableRateLimit": True,
    })

exchange = get_exchange()

# ------------------------------------------------------------
# LOGIQUE RUN
# ------------------------------------------------------------
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
        bal = exchange.fetch_balance()
        usdc = bal["free"].get("USDC", 0)
        xrp  = bal["free"].get("XRP", 0)
        
        st.session_state.price = price
        st.session_state.usdc = usdc
        st.session_state.xrp = xrp

        if not st.session_state.run: return

        for i, bot in st.session_state.bots.items():
            if not bot["actif"]: continue

            if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                if usdc >= bot["mise"]:
                    qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.985) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"], bot["etape"] = qty, "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                    log(f"[Bot {i}] ACHAT OK")

            elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.99))
                exchange.create_market_sell_order(symbol, qty_sell)
                gain = ((bot["p_vente"] - bot["p_achat"]) * bot["qty"]) - (bot["mise"] * 0.006)
                bot["gain_cumule"] += gain
                bot["cycles"] += 1
                bot["qty"], bot["etape"] = 0, "ATTENTE_ACHAT"
                save_config(st.session_state.bots)
                log(f"[Bot {i}] VENTE OK gain={gain:.4f}")
    except Exception as e:
        log(f"Erreur: {e}")

run_cycle()

# ------------------------------------------------------------
# UI (CORRECTIONS APPLIQUÉES ICI)
# ------------------------------------------------------------
st.title("🚀 XRP Sniper Pro")

with st.sidebar:
    id_bot = st.selectbox("Bot n°", range(1, 51))
    bot = st.session_state.bots[id_bot]
    bot["actif"] = st.toggle("Activer", bot["actif"])
    bot["p_achat"] = st.number_input("Prix Achat", value=float(bot["p_achat"]), format="%.4f")
    bot["p_vente"] = st.number_input("Prix Vente", value=float(bot["p_vente"]), format="%.4f")
    bot["mise"] = st.number_input("Mise", value=float(bot["mise"]))
    if st.button("💾 Sauvegarder"): save_config(st.session_state.bots)
    st.button("🚀 Démarrer", on_click=lambda: st.session_state.update(run=True))
    st.button("🛑 Stop", on_click=lambda: st.session_state.update(run=False))

p, u, x = st.session_state.get("price", 0), st.session_state.get("usdc", 0), st.session_state.get("xrp", 0)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Prix XRP", f"{p:.4f}")
c2.metric("USDC", f"{u:.2f}")
c3.metric("XRP", f"{x:.2f}")
c4.metric("Gain Total", f"{sum(b['gain_cumule'] for b in st.session_state.bots.values()):.2f}")

st.divider()

# CORRECTION DE L'AFFICHAGE DES COLONNES
cols_ratio = [0.5, 1.2, 1, 1, 0.8, 0.8, 1, 1]
h = st.columns(cols_ratio)
titles = ["ID", "État", "Achat", "Vente", "Mise", "Qty", "Cycles", "Gain"]
for col, t in zip(h, titles): col.write(f"**{t}**")

for i, b in st.session_state.bots.items():
    if b["actif"]:
        row = st.columns(cols_ratio)
        row[0].write(str(i))
        row[1].write(b["etape"])
        row[2].write(f"{b['p_achat']:.4f}")
        row[3].write(f"{b['p_vente']:.4f}")
        row[4].write(f"{b['mise']}")
        row[5].write(f"{b['qty']:.2f}")
        row[6].write(str(b['cycles']))
        row[7].write(f"{b['gain_cumule']:.4f}")

st.subheader("📜 Logs")
st.code("\n".join(st.session_state.logs[::-1]))
