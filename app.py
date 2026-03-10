import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIGURATION DE LA PAGE
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro", layout="wide")
DB_FILE = "config_bots_xrp_secure.json"
BACKUP_FILE = "backup_config.json"
symbol = "XRP/USDC"

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# ------------------------------------------------------------
# AUTO-REFRESH (ST CLOUD SAFE)
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
# GESTION DU CONFIG JSON
# ------------------------------------------------------------
def save_config(bots):
    try:
        with open(BACKUP_FILE, "w") as bkp:
            json.dump(bots, bkp)
        if isinstance(bots, dict) and len(bots) > 0:
            with open(DB_FILE, "w") as f:
                json.dump(bots, f)
    except Exception as e:
        st.error(f"Erreur sauvegarde : {e}")

def load_config():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
            return {int(k): v for k, v in data.items()}
        except:
            if os.path.exists(BACKUP_FILE):
                with open(BACKUP_FILE, "r") as f:
                    backup = json.load(f)
                return {int(k): v for k, v in backup.items()}
    return None

# ------------------------------------------------------------
# INITIALISATION
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

if "run" not in st.session_state:
    st.session_state.run = False

# ------------------------------------------------------------
# ÉCHANGE KRAKEN
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
# LOGIQUE DE TRADING
# ------------------------------------------------------------
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
        bal = exchange.fetch_balance()
        usdc = bal["free"].get("USDC", 0)
        xrp = bal["free"].get("XRP", 0)
        
        st.session_state.price = price
        st.session_state.usdc = usdc
        st.session_state.xrp = xrp

        if st.session_state.run:
            for i, bot in st.session_state.bots.items():
                if not bot["actif"]: continue

                # ACHAT
                if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                    if usdc >= bot["mise"]:
                        qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.98) / price))
                        exchange.create_market_buy_order(symbol, qty)
                        bot["qty"] = qty
                        bot["etape"] = "ATTENTE_VENTE"
                        save_config(st.session_state.bots)
                        log(f"Bot {i} : ACHAT effectué")

                # VENTE
                elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.99))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    bot["gain_cumule"] += (bot["p_vente"] - bot["p_achat"]) * bot["qty"]
                    bot["cycles"] += 1
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"Bot {i} : VENTE effectuée")
    except Exception as e:
        log(f"Erreur API : {e}")

run_cycle()

# ------------------------------------------------------------
# INTERFACE (UI)
# ------------------------------------------------------------
is_running = st.session_state.run and any(b["actif"] for b in st.session_state.bots.values())
status_color = "#00FF00" if is_running else "#444444"

# TITRE AVEC BOULE LUMINEUSE
st.markdown(f"""
    <div style="display: flex; align-items: center;">
        <h1 style="margin: 0;">🚀 XRP Sniper Pro</h1>
        <span style="height: 18px; width: 18px; background-color: {status_color}; border-radius: 50%; 
        display: inline-block; margin-left: 15px; margin-top: 12px; box-shadow: 0 0 12px {status_color};"></span>
    </div><br>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ CONFIGURATION")
    id_bot = st.selectbox("Sélectionner Bot", range(1, 51))
    bot = st.session_state.bots[id_bot]
    
    bot["actif"] = st.toggle("Activer Bot", bot["actif"])
    bot["p_achat"] = st.number_input("Prix Achat", value=bot["p_achat"], format="%.4f")
    bot["p_vente"] = st.number_input("Prix Vente", value=bot["p_vente"], format="%.4f")
    bot["mise"] = st.number_input("Mise USDC", value=bot["mise"])

    if st.button("💾 Sauvegarder Config"):
        save_config(st.session_state.bots)
        st.success("Config enregistrée")

    st.divider()
    if st.button("🚀 DÉMARRER TOUT", use_container_width=True):
        st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True):
        st.session_state.run = False

# METRICS
p = st.session_state.get("price", 0)
u = st.session_state.get("usdc", 0)
x = st.session_state.get("xrp", 0)
g = sum(b["gain_cumule"] for b in st.session_state.bots.values())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Prix XRP", f"{p:.4f} $" if p else "---")
c2.metric("Solde USDC", f"{u:.2f} $")
c3.metric("Solde XRP", f"{x:.2f}")
c4.metric("Gain Total", f"{g:.2f} $")

st.divider()

# TABLEAU DES BOTS ACTIFS
cols = st.columns([0.5, 1, 1, 1, 1, 1])
fields = ["ID", "Statut", "Achat", "Vente", "Cycles", "Gain"]
for col, field in zip(cols, fields): col.write(f"**{field}**")

for i, b in st.session_state.bots.items():
    if b["actif"] or b["cycles"] > 0:
        c = st.columns([0.5, 1, 1, 1, 1, 1])
        c.write(f"#{i}")
        c.write("✅" if b["actif"] else "❌")
        c.write(f"{b['p_achat']}")
        c.write(f"{b['p_vente']}")
        c.write(f"{b['cycles']}")
        c.write(f"{b['gain_cumule']:.2f}")

auto_refresh()
