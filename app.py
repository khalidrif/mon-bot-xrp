import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro 🚀", layout="wide")
DB_FILE = "config_bots_xrp_secure.json"
symbol = "XRP/USDC"

# Masquer le bouton refresh et styliser les métriques
st.markdown("""
    <style>
    button[kind="secondary"] { display: none !important; }
    .stMetric { background: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")
    if len(st.session_state.logs) > 20: st.session_state.logs.pop(0)

# ------------------------------------------------------------
# AUTO-REFRESH (1 SECONDE)
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
# GESTION CONFIG
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
        except: return None
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
        
        # Delta pour l'affichage
        old_p = st.session_state.get("price", price)
        st.session_state.diff = price - old_p
        st.session_state.price = price
        
        bal = exchange.fetch_balance()
        st.session_state.usdc = bal["free"].get("USDC", 0)
        st.session_state.xrp = bal["free"].get("XRP", 0)

        if not st.session_state.run: return

        for i, bot in st.session_state.bots.items():
            if not bot["actif"]: continue

            # ACHAT
            if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                if st.session_state.usdc >= bot["mise"]:
                    qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.99) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"] = qty
                    bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                    log(f"✅ [Bot {i}] ACHAT à {price}")

            # VENTE
            elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                if bot["qty"] > 0:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
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
# INTERFACE (UI)
# ------------------------------------------------------------
st.title("🚀 XRP Sniper Pro")

with st.sidebar:
    st.header("⚙️ Contrôle")
    if not st.session_state.run:
        if st.button("▶️ DÉMARRER", use_container_width=True):
            st.session_state.run = True
            st.rerun()
    else:
        if st.button("🛑 STOPPER", use_container_width=True):
            st.session_state.run = False
            st.rerun()
    
    st.divider()
    id_bot = st.selectbox("Bot #", range(1, 51))
    bot = st.session_state.bots[id_bot]
    bot["actif"] = st.toggle("Activer", bot["actif"])
    bot["p_achat"] = st.number_input("Achat", value=float(bot["p_achat"]), format="%.4f")
    bot["p_vente"] = st.number_input("Vente", value=float(bot["p_vente"]), format="%.4f")
    bot["mise"] = st.number_input("Mise (USDC)", value=float(bot["mise"]))
    if st.button("💾 Sauver"):
        save_config(st.session_state.bots)
        st.toast("Sauvegardé !")

# Metrics
p = st.session_state.get("price", 0)
d = st.session_state.get("diff", 0)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Prix XRP", f"{p:.5f}", delta=f"{d:.5f}")
m2.metric("USDC", f"{st.session_state.get('usdc', 0):.2f}")
m3.metric("XRP", f"{st.session_state.get('xrp', 0):.2f}")
m4.metric("Total Profit", f"{sum(b['gain_cumule'] for b in st.session_state.bots.values()):.4f}")

# Table des bots corrigée
st.divider()
st.subheader("🤖 Bots Actifs")
h0, h1, h2, h3, h4, h5, h6 = st.columns([0.5, 1, 1, 1, 1, 1, 1])
for col, text in zip([h0,h1,h2,h3,h4,h5,h6], ["ID", "Statut", "Achat", "Vente", "Mise", "Cycles", "Gain"]):
    col.write(f"**{text}**")

for i, b in st.session_state.bots.items():
    if b.get("actif"):
        c0, c1, c2, c3, c4, c5, c6 = st.columns([0.5, 1, 1, 1, 1, 1, 1])
        c0.write(str(i))
        c1.write("🔵 VENTE" if b["etape"] == "ATTENTE_VENTE" else "🟢 ACHAT")
        c2.write(f"{b['p_achat']:.4f}")
        c3.write(f"{b['p_vente']:.4f}")
        c4.write(f"{b['mise']:.2f}")
        c5.write(str(b['cycles']))
        c6.write(f"{b['gain_cumule']:.4f}")

st.divider()
st.subheader("📜 Logs")
st.code("\n".join(st.session_state.logs[::-1]))
