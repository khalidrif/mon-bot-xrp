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
    if len(st.session_state.logs) > 20: st.session_state.logs.pop(0)

# ------------------------------------------------------------
# PERSISTENCE JSON
# ------------------------------------------------------------
def save_config(bots):
    try:
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
            return None
    return None

# ------------------------------------------------------------
# INITIALISATION DES BOTS (50)
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
            } for i in range(1, 51)
        }

if "run" not in st.session_state:
    st.session_state.run = False

# ------------------------------------------------------------
# CONNEXION KRAKEN
# ------------------------------------------------------------
@st.cache_resource
def get_exchange():
    try:
        ex = ccxt.kraken({
            "apiKey": st.secrets["KRAKEN_API_KEY"],
            "secret": st.secrets["KRAKEN_API_SECRET"],
            "enableRateLimit": True,
        })
        return ex
    except Exception as e:
        st.error(f"Erreur API Key : {e}")
        return None

exchange = get_exchange()

# ------------------------------------------------------------
# LOGIQUE DE TRADING
# ------------------------------------------------------------
def run_cycle():
    if not exchange: return

    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        price = ticker["last"]
        bal = exchange.fetch_balance()
        usdc = bal["free"].get("USDC", 0)
        xrp = bal["free"].get("XRP", 0)
        
        st.session_state.price = price
        st.session_state.usdc = usdc
        st.session_state.xrp = xrp
    except Exception as e:
        log(f"Erreur réseau/API : {e}")
        return

    if not st.session_state.run:
        return

    for i, bot in st.session_state.bots.items():
        if not bot["actif"]:
            continue

        # --- LOGIQUE ACHAT ---
        if bot["etape"] == "ATTENTE_ACHAT":
            if price <= bot["p_achat"]:
                if usdc >= bot["mise"]:
                    try:
                        qty = float(exchange.amount_to_precision(SYMBOL, (bot["mise"] * 0.99) / price))
                        exchange.create_market_buy_order(SYMBOL, qty)
                        bot["qty"] = qty
                        bot["etape"] = "ATTENTE_VENTE"
                        save_config(st.session_state.bots)
                        log(f"✅ Bot {i} : Achat réussi ({qty} XRP)")
                    except Exception as e:
                        log(f"❌ Bot {i} Erreur Achat : {e}")

        # --- LOGIQUE VENTE ---
        elif bot["etape"] == "ATTENTE_VENTE":
            if price >= bot["p_vente"] and bot["qty"] > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(SYMBOL, bot["qty"]))
                    exchange.create_market_sell_order(SYMBOL, qty_sell)
                    
                    # Calcul de gain corrigé (Vente - Achat)
                    gain_net = (bot["p_vente"] - bot["p_achat"]) * bot["qty"]
                    bot["gain_cumule"] += gain_net
                    bot["cycles"] += 1
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"💰 Bot {i} : Vente réussie (+{gain_net:.2f} USDC)")
                except Exception as e:
                    log(f"❌ Bot {i} Erreur Vente : {e}")

run_cycle()

# ------------------------------------------------------------
# INTERFACE UTILISATEUR (UI)
# ------------------------------------------------------------
st.title("🚀 XRP Sniper Pro Multi-Bots")

# SIDEBAR : Configuration
with st.sidebar:
    st.header("⚙️ Paramètres")
    id_bot = st.selectbox("Sélectionner Bot", range(1, 51))
    bot_sel = st.session_state.bots[id_bot]

    bot_sel["actif"] = st.toggle("Activer le Bot", bot_sel["actif"])
    bot_sel["p_achat"] = st.number_input("Prix Achat", value=bot_sel["p_achat"], format="%.4f")
    bot_sel["p_vente"] = st.number_input("Prix Vente", value=bot_sel["p_vente"], format="%.4f")
    bot_sel["mise"] = st.number_input("Mise (USDC)", value=bot_sel["mise"])

    if st.button("💾 Sauvegarder Config"):
        save_config(st.session_state.bots)
        st.success("Config enregistrée !")

    st.divider()
    if not st.session_state.run:
        if st.button("▶️ DÉMARRER TOUS LES BOTS", use_container_width=True):
            st.session_state.run = True
            st.rerun()
    else:
        if st.button("🛑 ARRÊTER TOUS LES BOTS", type="primary", use_container_width=True):
            st.session_state.run = False
            st.rerun()

# DASHBOARD : Stats
p = st.session_state.get("price", 0)
u = st.session_state.get("usdc", 0)
x = st.session_state.get("xrp", 0)
total_g = sum(b["gain_cumule"] for b in st.session_state.bots.values())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Prix XRP", f"{p:.4f} $" if p else "Chargement...")
m2.metric("Solde USDC", f"{u:.2f} $")
m3.metric("Solde XRP", f"{x:.2f}")
m4.metric("Profit Total", f"{total_g:.2f} $", delta=f"{total_g:.2f}")

st.divider()

# TABLEAU DE SURVEILLANCE
st.subheader("📊 État des Bots")
cols = st.columns([0.4, 0.4, 1, 1, 1, 1, 1])
cols[0].write("**ID**")
cols[1].write("**Statut**")
cols[2].write("**Étape**")
cols[3].write("**P. Achat**")
cols[4].write("**P. Vente**")
cols[5].write("**Mise**")
cols[6].write("**Gain**")

for i, b in st.session_state.bots.items():
    # On affiche les bots actifs ou ceux qui ont déjà bossé
    if b["actif"] or b["cycles"] > 0:
        c = st.columns([0.4, 0.4, 1, 1, 1, 1, 1])
        c[0].write(f"#{i}")
        # LE BOUTON VERT/ROUGE ICI
        c[1].write("🟢" if b["actif"] else "🔴")
        c[2].info(b["etape"])
        c[3].write(f"{b['p_achat']:.4f}")
        c[4].write(f"{b['p_vente']:.4f}")
        c[5].write(f"{b['mise']}$")
        c[6].write(f"**{b['gain_cumule']:.2f}$** ({b['cycles']} 🔄)")

# LOGS
with st.expander("📝 Journaux d'activité (Logs)"):
    for l in reversed(st.session_state.logs):
        st.text(l)

# AUTO-REFRESH
time.sleep(2)
st.rerun()
