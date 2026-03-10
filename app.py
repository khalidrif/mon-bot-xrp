import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIGURATION ET STYLE
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro 🚀", layout="wide")
DB_FILE = "config_bots_xrp_secure.json"
symbol = "XRP/USDC"

# Style pour masquer le bouton refresh et stabiliser l'UI
st.markdown("""
    <style>
    div[data-testid="stButton"] button[kind="secondary"] { display: none; }
    .stMetric { background: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")
    if len(st.session_state.logs) > 30: st.session_state.logs.pop(0)

# ------------------------------------------------------------
# AUTO-REFRESH ULTRA-RAPIDE (1 SECONDE)
# ------------------------------------------------------------
def auto_refresh():
    st.markdown("""
        <script>
            setTimeout(function() {
                window.parent.document.querySelectorAll('button').forEach(function(btn) {
                    if (btn.innerText === 'refresh_hidden') { btn.click(); }
                });
            }, 1000);
        </script>
    """, unsafe_allow_html=True)
    st.button("refresh_hidden", key="refresh_button")

auto_refresh()

# ------------------------------------------------------------
# GESTION CONFIGURATION
# ------------------------------------------------------------
def save_config(bots):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(bots, f)
    except Exception as e:
        st.error(f"Erreur sauvegarde: {e}")

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
# INITIALISATION
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
# EXCHANGE (KRAKEN)
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
        
        # Calcul du mouvement pour l'affichage
        if "old_price" not in st.session_state: st.session_state.old_price = price
        st.session_state.diff = price - st.session_state.old_price
        st.session_state.old_price = price
        
        bal = exchange.fetch_balance()
        usdc = bal["free"].get("USDC", 0)
        xrp = bal["free"].get("XRP", 0)
        
        st.session_state.price = price
        st.session_state.usdc = usdc
        st.session_state.xrp = xrp

        if not st.session_state.run:
            return

        for i, bot in st.session_state.bots.items():
            if not bot["actif"]: continue

            # ACHAT
            if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                if usdc >= bot["mise"]:
                    qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.99) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"] = qty
                    bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                    log(f"✅ [Bot {i}] ACHAT effectué à {price}")

            # VENTE
            elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                if bot["qty"] > 0:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    
                    # Correction calcul gain : (Vente - Achat)
                    profit = ((price - bot["p_achat"]) * bot["qty"]) - (bot["mise"] * 0.004)
                    bot["gain_cumule"] += profit
                    bot["cycles"] += 1
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"💰 [Bot {i}] VENTE OK | Profit: {profit:.4f}")

    except Exception as e:
        log(f"⚠️ Erreur: {str(e)}")

run_cycle()

# ------------------------------------------------------------
# INTERFACE UTILISATEUR (UI)
# ------------------------------------------------------------
st.title("🚀 XRP Sniper Pro")

# Barre latérale
with st.sidebar:
    st.header("⚙️ Contrôle")
    if not st.session_state.run:
        if st.button("▶️ DÉMARRER LES BOTS", use_container_width=True):
            st.session_state.run = True
            st.rerun()
    else:
        if st.button("🛑 STOPPER LES BOTS", use_container_width=True):
            st.session_state.run = False
            st.rerun()
    
    st.divider()
    id_bot = st.selectbox("Configurer Bot #", range(1, 51))
    bot = st.session_state.bots[id_bot]
    
    bot["actif"] = st.toggle("Activer ce bot", bot["actif"])
    bot["p_achat"] = st.number_input("Prix Achat", value=float(bot["p_achat"]), format="%.4f")
    bot["p_vente"] = st.number_input("Prix Vente", value=float(bot["p_vente"]), format="%.4f")
    bot["mise"] = st.number_input("Mise (USDC)", value=float(bot["mise"]))
    
    if st.button("💾 Sauvegarder Config"):
        save_config(st.session_state.bots)
        st.success("Config bot mise à jour !")

# Dashboard
p = st.session_state.get("price", 0)
diff = st.session_state.get("diff", 0)
gain_total = sum(b["gain_cumule"] for b in st.session_state.bots.values())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Prix XRP/USDC", f"{p:.5f}", delta=f"{diff:.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc', 0):.2f}")
m3.metric("Solde XRP", f"{st.session_state.get('xrp', 0):.2f}")
m4.metric("Profit Total", f"{gain_total:.4f} USDC")

# Table des bots
st.divider()
st.subheader("🤖 État des Bots Actifs")
cols = st.columns([0.5, 1, 1, 1, 1, 1, 1])
fields = ["ID", "Statut", "Achat", "Vente", "Mise", "Cycles", "Gain"]
for col, field in zip(cols, fields): col.write(f"**{field}**")

for i, b in st.session_state.bots.items():
    if b["actif"]:
        c = st.columns([0.5, 1, 1, 1, 1, 1, 1])
        c.write(i)
        c.write("🔵 VENTE" if b["etape"] == "ATTENTE_VENTE" else "🟢 ACHAT")
        c.write(f"{b['p_achat']}")
        c.write(f"{b['p_vente']}")
        c.write(f"{b['mise']}")
        c.write(f"{b['cycles']}")
        c.write(f"{b['gain_cumule']:.4f}")

# Logs
st.divider()
st.subheader("📜 Logs d'activité")
st.code("\n".join(st.session_state.logs[::-1]))
