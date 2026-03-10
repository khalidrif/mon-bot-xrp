import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro ", layout="wide")
DB_FILE = "config_bots_xrp_secure.json"
symbol = "XRP/USDC"

# LOGS POUR DEBUG
if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# ------------------------------------------------------------
# AUTO-REFRESH STREAMLIT CLOUD SAFE
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

auto_refresh()

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
            }
            for i in range(1, 51)
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
# RUN 1 CYCLE (TRADE)
# ------------------------------------------------------------
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
        bal = exchange.fetch_balance()
        usdc = bal["free"].get("USDC", 0)
        xrp  = bal["free"].get("XRP", 0)
        st.session_state.price, st.session_state.usdc, st.session_state.xrp = price, usdc, xrp
    except:
        price = st.session_state.get("price")

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot["actif"]: continue
        if bot["etape"] == "ATTENTE_ACHAT" and price and price <= bot["p_achat"]:
            if st.session_state.usdc >= bot["mise"]:
                try:
                    qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.985) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"], bot["etape"] = qty, "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                except: pass
        elif bot["etape"] == "ATTENTE_VENTE" and price and price >= bot["p_vente"]:
            if bot["qty"] > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.99))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    bot["gain_cumule"] += (bot["p_vente"] - bot["p_achat"]) * bot["qty"]
                    bot["cycles"] += 1
                    bot["qty"], bot["etape"] = 0, "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                except: pass

run_cycle()

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
# ... (ton code précédent : run_cycle, etc.)

run_cycle()

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
# REMPLACE TOUT LE BLOC CI-DESSOUS :

bot_en_cours = st.session_state.run and any(b["actif"] for b in st.session_state.bots.values())
dot_color = "#00FF00" if bot_en_cours else "#555555"
glow_effect = f"box-shadow: 0 0 15px {dot_color};" if bot_en_cours else ""

st.markdown(f"""
    <style>
    @keyframes pulse {{
        0% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
        100% {{ opacity: 1; }}
    }}
    .status-dot {{
        width: 18px; 
        height: 18px; 
        background-color: {dot_color}; 
        border-radius: 50%; 
        margin-left: 15px; 
        margin-top: 10px;
        {glow_effect}
        animation: {"pulse 2s infinite" if bot_en_cours else "none"};
    }}
    </style>
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">🚀 XRP Sniper Pro</h1>
        <div class="status-dot"></div>
    </div>
    """, unsafe_allow_html=True)

# LA SUITE DE TON CODE (avec with st.sidebar:) ...


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

cols = st.columns([0.4, 1.2, 1, 1, 0.8, 0.8, 1, 0.6])
headers = ["ID", "Actif", "Achat", "Vente", "Mise", "Etape", "Cycles", "Gain"]
for col, h in zip(cols, headers): col.write(f"**{h}**")

for i, b in st.session_state.bots.items():
    if b["actif"] or b["cycles"] > 0:
        r = st.columns([0.4, 1.2, 1, 1, 0.8, 0.8, 1, 0.6])
        r[0].write(f"#{i}")
        r[1].write("✅" if b["actif"] else "❌")
        r[2].write(f"{b['p_achat']:.4f}")
        r[3].write(f"{b['p_vente']:.4f}")
        r[4].write(f"{b['mise']}")
        r[5].write(f"{b['etape']}")
        r[6].write(f"{b['cycles']}")
        r[7].write(f"{b['gain_cumule']:.2f}")

