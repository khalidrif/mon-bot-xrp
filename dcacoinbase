import streamlit as st
import ccxt
import json
import os
import time
from streamlit_autorefresh import st_autorefresh

# === VERROU GLOBAL ===
@st.cache_resource
def obtenir_verrou_serveur():
    return {"achat_en_cours": False}

verrou_global = obtenir_verrou_serveur()

# === CONFIGURATION ===
st.set_page_config(page_title="⚡ DCA Sniper Coinbase", layout="centered")
symbol = "XRP/USDC"
CONFIG_FILE = "bots_config.json"
st_autorefresh(interval=20000, key="refresh_app")

# === LOGS ===
if "logs" not in st.session_state:
    st.session_state.logs = []
if "achat_en_cours" not in st.session_state:
    st.session_state.achat_en_cours = False

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# === JSON robust ===
def save_bots():
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(st.session_state.bots, f, indent=2)
    except Exception as e:
        log(f"Erreur sauvegarde JSON : {e}")

def load_bots():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    except:
        return {}

# === CONNEXION COINBASE ===
@st.cache_resource
def get_exchange():
    return ccxt.coinbaseadvanced({
        "apiKey": st.secrets["COINBASE_API_KEY"],
        "secret": st.secrets["COINBASE_API_SECRET"],
        "enableRateLimit": True
    })

exchange = get_exchange()

# === INIT BOTS ===
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

for b in st.session_state.bots.values():
    b.setdefault("actif", True)
    b.setdefault("etape", "ACHAT")
    b.setdefault("investi", 0.0)
    b.setdefault("gain_net", 0.0)
    b.setdefault("cycles", 0)

save_bots()

# === PRIX LIVE + SOLDES ===
try:
    ticker = exchange.fetch_ticker(symbol)
    bid, ask = ticker["bid"], ticker["ask"]
    mid = (bid + ask) / 2
except:
    bid = ask = mid = 0.0
    log("Erreur prix Coinbase")

# Soldes
try:
    balances = exchange.fetch_balance()
    usdc = float(balances["free"].get("USDC", 0))
    xrp = float(balances["free"].get("XRP", 0))
except:
    usdc = xrp = 0.0

wallet_total = usdc + xrp * mid

# === HEADER ===
st.title("🚀 DCA Sniper Pro – Coinbase")
col1, col2, col3 = st.columns(3)
col1.metric("USDC", f"{usdc:.2f}$")
col2.metric("XRP", f"{xrp:.2f}")
col3.metric("Valeur totale", f"{wallet_total:.2f}$")
st.caption(f"Prix XRP {mid:.5f} | MAJ {time.strftime('%H:%M:%S')}")
st.divider()

# === AJOUT D’UN BOT ===
st.subheader("➕ Ajouter un bot")
c1, c2, c3, c4 = st.columns(4)

with c1:
    p_achat_new = st.number_input("Prix Achat", value=1.00000, step=0.00001, format="%.5f")
with c2:
    pct_profit_new = st.number_input("Profit net (%)", value=3.0, step=0.1)
with c3:
    max_invest_new = st.number_input("Max investi (USDC)", value=50.0, step=1.0)
with c4:
    mise_initiale = st.number_input("Mise initiale ($)", value=10.0, step=0.5)

if st.button("Créer le bot"):
    next_id = max(st.session_state.bots.keys()) + 1 if st.session_state.bots else 1
    st.session_state.bots[next_id] = {
        "id": next_id,
        "p_achat": p_achat_new,
        "pct_profit": pct_profit_new,
        "max_invest": max_invest_new,
        "mise": mise_initiale,
        "investi": 0.0,
        "gain_net": 0.0,
        "cycles": 0,
        "actif": True,
        "etape": "ACHAT"
    }
    save_bots()
    log(f"Bot {next_id} créé.")
    st.rerun()

# === LOGIQUE TRADING ===
for i, b in st.session_state.bots.items():
    if not b["actif"]:
        continue

    # Precision Coinbase
    try:
        market = exchange.market(symbol)
        prec = market.get("precision", {}).get("amount", 4)
        qty_precision = int(prec)
    except:
        qty_precision = 4

    # ACHAT
    if b["etape"] == "ACHAT" and mid <= b["p_achat"]:

        montant_possible = b["max_invest"] - b["investi"]
        montant = min(b["mise"], montant_possible)

        if montant > 1 and usdc >= montant and not verrou_global["achat_en_cours"]:
            verrou_global["achat_en_cours"] = True
            b["etape"] = "EN_COURS_ACHAT"
            save_bots()

            try:
                qty = round(montant / b["p_achat"], qty_precision)
                exchange.create_limit_buy_order(symbol, qty, b["p_achat"])
                b["investi"] += montant
                b["etape"] = "VENTE"
                log(f"Bot {i} : Achat {qty} XRP pour {montant}$")
            except Exception as e:
                log(f"Erreur achat bot {i} : {e}")
                b["etape"] = "ACHAT"
            finally:
                verrou_global["achat_en_cours"] = False
                save_bots()

    # VENTE
    prix_vente_cible = b["p_achat"] * (1 + b["pct_profit"] / 100)

    if b["etape"] == "VENTE" and mid >= prix_vente_cible:

        if not verrou_global["achat_en_cours"]:

            verrou_global["achat_en_cours"] = True
            b["etape"] = "EN_COURS_VENTE"
            save_bots()

            try:
                qty_sell = round(b["investi"] / b["p_achat"], qty_precision)
                exchange.create_limit_sell_order(symbol, qty_sell, prix_vente_cible)

                gain = b["investi"] * (b["pct_profit"] / 100)
                b["gain_net"] += gain
                b["cycles"] += 1
                b["mise"] += gain
                b["investi"] = 0.0
                b["etape"] = "ACHAT"

                log(f"Bot {i} : Vente {qty_sell} XRP (+{gain:.2f}$)")
            except Exception as e:
                log(f"Erreur vente bot {i} : {e}")
                b["etape"] = "VENTE"
            finally:
                verrou_global["achat_en_cours"] = False
                save_bots()

# === TOTAL GAINS ===
total_gain = sum(b["gain_net"] for b in st.session_state.bots.values())
st.success(f"Gains cumulés : {total_gain:.2f}$")
st.divider()

# === AFFICHAGE DES BOTS ===
st.subheader("Bots actifs")
for i, b in sorted(st.session_state.bots.items()):
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.info(
            f"Bot {i} | Achat {b['p_achat']:.5f} | Profit {b['pct_profit']}% | "
            f"Mise {b['mise']:.2f}$ | Max {b['max_invest']:.2f}$ | "
            f"Investi {b['investi']:.2f}$ | Gain {b['gain_net']:.2f}$ | Cycles {b['cycles']} | {b['etape']}"
        )

    with col2:
        toggle = "🛑" if b["actif"] else "🚀"
        if st.button(toggle, key=f"toggle_{i}"):
            b["actif"] = not b["actif"]
            save_bots()
            st.rerun()

    with col3:
        if st.button("🗑️", key=f"del_{i}"):
            del st.session_state.bots[i]
            save_bots()
            st.rerun()

# === LOGS ===
st.divider()
st.subheader("Journal")
if st.session_state.logs:
    st.text_area("Logs", "\n".join(reversed(st.session_state.logs[-200:])), height=220)
