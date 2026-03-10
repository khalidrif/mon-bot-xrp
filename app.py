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
    st.button("refresh", key="refresh_button", help="Bouton de rafraîchissement automatique")

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
        usdc = bal["total"].get("USDC", 0) # 'total' est plus fiable que 'free' pour l'UI
        xrp = bal["total"].get("XRP", 0)
        
        st.session_state.price = price
        st.session_state.usdc = usdc
        st.session_state.xrp = xrp

        if st.session_state.run:
            for i, bot in st.session_state.bots.items():
                if not bot["actif"]: continue

                # ACHAT
                if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                    # On vérifie le solde USDC réel avant
                    if bal["free"].get("USDC", 0) >= bot["mise"]:
                        qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.98) / price))
                        exchange.create_market_buy_order(symbol, qty)
                        bot["qty"] = qty
                        bot["etape"] = "ATTENTE_VENTE"
                        save_config(st.session_state.bots)
                        log(f"Bot {i} : ACHAT {qty} XRP à {price}")

                # VENTE
                elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                    if bot["qty"] > 0:
                        qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.99))
                        exchange.create_market_sell_order(symbol, qty_sell)
                        gain = (bot["p_vente"] - bot["p_achat"]) * bot["qty"]
                        bot["gain_cumule"] += gain
                        bot["cycles"] += 1
                        bot["qty"] = 0
                        bot["etape"] = "ATTENTE_ACHAT"
                        save_config(st.session_state.bots)
                        log(f"Bot {i} : VENTE effectuée | Gain: {gain:.2f}")
    except Exception as e:
        log(f"Erreur API : {e}")

run_cycle()

# ------------------------------------------------------------
# INTERFACE (UI)
# ------------------------------------------------------------
# INDICATEUR BOULE VERTE/GRISE
is_running = st.session_state.run and any(b["actif"] for b in st.session_state.bots.values())
status_color = "#00FF00" if is_running else "#444444"

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
    bot["p_achat"] = st.number_input("Prix Achat", value=float(bot["p_achat"]), format="%.4f")
    bot["p_vente"] = st.number_input("Prix Vente", value=float(bot["p_vente"]), format="%.4f")
    bot["mise"] = st.number_input("Mise USDC", value=float(bot["mise"]))

    if st.button("💾 Sauvegarder Config"):
        save_config(st.session_state.bots)
        st.success(f"Bot {id_bot} enregistré")

    st.divider()
    if st.button("🚀 DÉMARRER TOUT", use_container_width=True):
        st.session_state.run = True
        st.rerun()
    if st.button("🛑 STOP TOUT", use_container_width=True):
        st.session_state.run = False
        st.rerun()

# METRICS PRINCIPALES
p = st.session_state.get("price", 0)
u = st.session_state.get("usdc", 0)
x = st.session_state.get("xrp", 0)
g = sum(b.get("gain_cumule", 0.0) for b in st.session_state.bots.values())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Prix XRP", f"{p:.4f} $" if p else "---")
m2.metric("Solde USDC", f"{u:.2f} $")
m3.metric("Solde XRP", f"{x:.2f}")
m4.metric("Gain Total", f"{g:.2f} $")

st.divider()

# TABLEAU DES BOTS (CORRIGÉ SANS ATTRIBUTEERROR)
st.subheader("🤖 État des Bots")
t1, t2, t3, t4, t5, t6 = st.columns([0.5, 1, 1, 1, 1, 1])
t1.write("**ID**")
t2.write("**Statut**")
t3.write("**Achat**")
t4.write("**Vente**")
t5.write("**Cycles**")
t6.write("**Gain**")

for i, b in st.session_state.bots.items():
    if b["actif"] or b.get("cycles", 0) > 0:
        c_id, c_st, c_ac, c_ve, c_cy, c_ga = st.columns([0.5, 1, 1, 1, 1, 1])
        c_id.write(f"#{i}")
        c_st.write("🟢 Actif" if b["actif"] else "⚪ Off")
        c_ac.write(f"{b['p_achat']:.4f}")
        c_ve.write(f"{b['p_vente']:.4f}")
        c_cy.write(f"{b.get('cycles', 0)}")
        c_ga.write(f"{b.get('gain_cumule', 0.0):.2f} $")

# LOGS SYSTEME
st.divider()
with st.expander("📜 Logs du système"):
    for l in reversed(st.session_state.logs[-15:]):
        st.text(l)

auto_refresh()
