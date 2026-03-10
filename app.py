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

# ------------------------------------------------------------
# AUTO-REFRESH
# ------------------------------------------------------------
def auto_refresh():
    st.markdown("""
        <script>
            setTimeout(function() {
                document.getElementById('refresh_button').click();
            }, 2000);
        </script>
    """, unsafe_allow_html=True)
    st.button("refresh", key="refresh_button")

# ------------------------------------------------------------
# JSON CONFIG
# ------------------------------------------------------------
def save_config(bots):
    try:
        with open("backup_config.json", "w") as bkp:
            json.dump(bots, bkp)
    except:
        pass
    if not isinstance(bots, dict) or len(bots) == 0:
        return
    try:
        with open(DB_FILE, "w") as f:
            json.dump(bots, f)
    except Exception as e:
        st.error(f"❌ ERREUR : {e}")

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
        "actif": False, "p_achat": 1.35, "p_vente": 1.38,
        "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0,
        "cycles": 0, "gain_cumule": 0.0,
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
            i: {
                "actif": False, "p_achat": 1.35, "p_vente": 1.38,
                "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0,
                "cycles": 0, "gain_cumule": 0.0
            } for i in range(1, 51)
        }
        save_config(st.session_state.bots)

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
        "enableRateLimit": True,
    })
    ex.load_markets()
    return ex

exchange = get_exchange()

# ------------------------------------------------------------
# RUN CYCLE
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

        if st.session_state.run:
            for i, bot in st.session_state.bots.items():
                if not bot["actif"]: continue
                # Logique Achat/Vente simplifiée
                if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"] and usdc >= bot["mise"]:
                    qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"], bot["etape"] = qty, "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"] and bot["qty"] > 0:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.99))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    bot["gain_cumule"] += (bot["p_vente"] - bot["p_achat"]) * bot["qty"]
                    bot["cycles"] += 1
                    bot["qty"], bot["etape"] = 0, "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
    except Exception as e:
        log(f"Erreur: {e}")

run_cycle()

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
# LOGIQUE BOULE VERTE
is_running = st.session_state.run and any(b["actif"] for b in st.session_state.bots.values())
status_color = "#00FF00" if is_running else "#444444"

st.markdown(f"""
    <div style="display: flex; align-items: center;">
        <h1 style="margin: 0;">🚀 XRP</h1>
        <span style="height: 18px; width: 18px; background-color: {status_color}; border-radius: 50%; 
        display: inline-block; margin-left: 15px; margin-top: 10px; box-shadow: 0 0 12px {status_color};"></span>
    </div><br>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ CONFIGURATION BOT")
    id_bot = st.selectbox("Bot n°", range(1, 51))
    bot = st.session_state.bots[id_bot]
    bot["actif"] = st.toggle("Activer", bot["actif"])
    bot["p_achat"] = st.number_input("Prix Achat", value=float(bot["p_achat"]), format="%.4f")
    bot["p_vente"] = st.number_input("Prix Vente", value=float(bot["p_vente"]), format="%.4f")
    bot["mise"] = st.number_input("Mise", value=float(bot["mise"]))
    if st.button("💾 Sauvegarder"):
        save_config(st.session_state.bots)
        st.toast("Sauvegardé ✔")
    if st.button("🗑 Supprimer ce bot"):
        reset_bot(id_bot)
    st.divider()
    st.button("🚀 Démarrer", on_click=lambda: st.session_state.update(run=True))
    st.button("🛑 Stop", on_click=lambda: st.session_state.update(run=False))

price = st.session_state.get("price")
usdc  = st.session_state.get("usdc", 0)
xrp   = st.session_state.get("xrp", 0)
gain_total = sum(b["gain_cumule"] for b in st.session_state.bots.values())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Prix XRP", f"{price:.4f}" if price else "...")
c2.metric("USDC", f"{usdc:.4f}")
c3.metric("XRP", f"{xrp:.4f}")
c4.metric("Gain Total", f"{gain_total:.4f}")

st.divider()

# Ton affichage d'origine (boucle for col)
cols = st.columns([0.5, 1, 1, 1, 1, 1, 1, 1])
headers = ["Bot", "Actif", "Achat", "Vente", "Mise", "Etape", "Cycles", "Gain"]
for col, h in zip(cols, headers):
    col.write(f"**{h}**")

for i, b in st.session_state.bots.items():
    if b["actif"] or b["cycles"] > 0:
        c = st.columns([0.5, 1, 1, 1, 1, 1, 1, 1])
        c[0].write(f"#{i}")
        c[1].write("✅" if b["actif"] else "❌")
        c[2].write(f"{b['p_achat']}")
        c[3].write(f"{b['p_vente']}")
        c[4].write(f"{b['mise']}")
        c[5].write(f"{b['etape']}")
        c[6].write(f"{b['cycles']}")
        c[7].write(f"{b['gain_cumule']:.2f}")

auto_refresh()
