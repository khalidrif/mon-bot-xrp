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
# AUTO-REFRESH STREAMLIT CLOUD SAFE (NO ERROR, NO FLICKER)
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
# JSON CONFIG AVEC BACKUP & PROTECTION
# ------------------------------------------------------------
def save_config(bots):
    try:
        with open("backup_config.json", "w") as bkp:
            json.dump(bots, bkp)
    except:
        pass

    if not isinstance(bots, dict) or len(bots) == 0:
        st.error("🔥 Tentative d'écraser avec fichier vide BLOQUÉE !")
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

            if not isinstance(data, dict) or len(data) == 0:
                raise ValueError("Config vide/corrompue")

            return {int(k): v for k, v in data.items()}

        except:
            st.warning("⚠️ Config corrompue → restauration backup…")

            if os.path.exists("backup_config.json"):
                try:
                    with open("backup_config.json", "r") as f:
                        backup = json.load(f)
                    st.success("✨ Backup restauré")
                    return {int(k): v for k, v in backup.items()}
                except:
                    st.error("❌ Backup illisible")
                    return None
            else:
                st.error("❌ Aucun backup trouvé")
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
    cfg = load_config()
    if cfg:
        st.session_state.bots = cfg
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
                "gain_cumule": 0.0
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
        log(f"Prix reçu : {price}")
    except Exception as e:
        price = None
        log(f"[ERREUR TICKER] {e}")

    try:
        bal = exchange.fetch_balance()
        usdc = bal["free"].get("USDC", 0)
        xrp  = bal["free"].get("XRP", 0)
        log(f"USDC={usdc} | XRP={xrp}")
    except Exception as e:
        usdc = 0
        xrp = 0
        log(f"[ERREUR BALANCE] {e}")

    st.session_state.price = price
    st.session_state.usdc = usdc
    st.session_state.xrp = xrp

    if not st.session_state.run:
        log("Bots arrêtés")
        return

    # Boucle des 50 bots
    for i, bot in st.session_state.bots.items():
        if not bot["actif"]:
            continue

        log(f"[Bot {i}] État={bot['etape']} Achat={bot['p_achat']} Vente={bot['p_vente']}")

        # ACHAT
        if bot["etape"] == "ATTENTE_ACHAT":
            if price and price <= bot["p_achat"]:
                if usdc >= bot["mise"]:
                    try:
                        mise_net = bot["mise"] * 0.985
                        qty = float(exchange.amount_to_precision(symbol, mise_net / price))
                        exchange.create_market_buy_order(symbol, qty)

                        bot["qty"] = qty
                        bot["etape"] = "ATTENTE_VENTE"
                        save_config(st.session_state.bots)
                        log(f"[Bot {i}] ACHAT OK qty={qty}")
                    except Exception as e:
                        log(f"[Bot {i}] ERREUR ACHAT : {e}")
                else:
                    log(f"[Bot {i}] Solde insuffisant USDC={usdc}")

        # VENTE
        if bot["etape"] == "ATTENTE_VENTE":
            if price and price >= bot["p_vente"] and bot["qty"] > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.99))
                    exchange.create_market_sell_order(symbol, qty_sell)

                    gain = ((bot["p_achat"] - bot["p_vente"]) * bot["qty"]) - (bot["mise"] * 0.006)

                    bot["gain_cumule"] += gain
                    bot["cycles"] += 1
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"[Bot {i}] VENTE OK gain={gain}")
                except Exception as e:
                    log(f"[Bot {i}] ERREUR VENTE : {e}")

run_cycle()

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("🚀 XRP")

with st.sidebar:
    st.header("⚙️ CONFIGURATION BOT")

    id_bot = st.selectbox("Bot n°", range(1, 51))
    bot = st.session_state.bots[id_bot]

    bot["actif"] = st.toggle("Activer", bot["actif"])
    bot["p_achat"] = st.number_input("Prix Achat", value=bot["p_achat"], format="%.4f")
    bot["p_vente"] = st.number_input("Prix Vente", value=bot["p_vente"], format="%.4f")
    bot["mise"] = st.number_input("Mise", value=bot["mise"])

    if st.button("💾 Sauvegarder"):
        save_config(st.session_state.bots)
        st.toast("Sauvegardé ✔")

    if st.button("🗑 Supprimer ce bot"):
        reset_bot(id_bot)

    st.divider()
    st.button("🚀 Démarrer", on_click=lambda: st.session_state.update(run=True))
    st.button("🛑 Stop", on_click=lambda: st.session_state.update(run=False))

price = st.session_state.get("price")
usdc  = st.session_state.get("usdc")
xrp   = st.session_state.get("xrp")
gain_total = sum(b["gain_cumule"] for b in st.session_state.bots.values())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Prix XRP", f"{price:.4f}" if price else "...")
c2.metric("USDC", f"{usdc:.4f}")
c3.metric("XRP", f"{xrp:.4f}")
c4.metric("Gain Total", f"{gain_total:.4f}")

st.divider()

cols = st.columns([0.4, 1.2, 1, 1, 0.8, 0.8, 1, 0.6])
for col, txt in zip(cols, ["N°", "État", "Achat", "Vente", "Mise", "Cycles", "Gain", ""]):
    col.write(f"**{txt}**")

for i, bot in st.session_state.bots.items():
    if bot["actif"]:
        c = st.columns([0.4, 1.2, 1, 1, 0.8, 0.8, 1, 0.6])
        c[0].write(i)
        c[1].write(bot["etape"])
        c[2].write(bot["p_achat"])
        c[3].write(bot["p_vente"])
        c[4].write(bot["mise"])
        c[5].write(bot["cycles"])
        c[6].write(round(bot["gain_cumule"], 4))
        if c[7].button("🗑", key=f"del_{i}"):
            reset_bot(i)

st.subheader("📝 LOGS EN DIRECT")
for line in st.session_state.logs[-40:]:
    st.write(line)



