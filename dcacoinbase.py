import streamlit as st
import ccxt
import json
import os
import time
from streamlit_autorefresh import st_autorefresh


# === VERROU GLOBAL ===
@st.cache_resource
def get_global_lock():
    return {"trade_lock": False}

verrou = get_global_lock()


# === CONFIG ===
st.set_page_config(page_title="⚡ DCA Multi‑Bots Coinbase", layout="centered")
symbol = "XRP/USDC"
CONFIG_FILE = "bots_config.json"
st_autorefresh(interval=20000, key="refresh")


# === LOGS ===
if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")


# === JSON ===
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
            return {int(k): v for k, v in json.load(f).items()}
    except:
        return {}


# === COINBASE ===
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
    b.setdefault("p_achat", 0.0)
    b.setdefault("pct_profit", 3.0)
    b.setdefault("paliers", [])
    b.setdefault("investi", 0.0)
    b.setdefault("gain_net", 0.0)
    b.setdefault("cycles", 0)
    b.setdefault("etape", "ACHAT")

save_bots()


# === PRIX & SOLDES ===
try:
    ticker = exchange.fetch_ticker(symbol)
    bid, ask = ticker["bid"], ticker["ask"]
    mid = (bid + ask) / 2
except:
    mid = bid = ask = 0.0
    log("Erreur récupération prix")

try:
    balances = exchange.fetch_balance()
    usdc = float(balances["free"].get("USDC", 0))
    xrp = float(balances["free"].get("XRP", 0))
except:
    usdc = xrp = 0.0

wallet_total = usdc + xrp * mid


# === HEADER ===
st.title("🚀 DCA Sniper Pro – Coinbase (Multi‑Bots)")

c1, c2, c3 = st.columns(3)
c1.metric("USDC disponible", f"{usdc:.2f}$")
c2.metric("XRP disponible", f"{xrp:.4f}")
c3.metric("Valeur totale", f"{wallet_total:.2f}$")

st.caption(f"Prix XRP : {mid:.5f} | MAJ {time.strftime('%H:%M:%S')}")
st.divider()


# === AJOUT BOT ===
st.subheader("➕ Ajouter un bot")

c1, c2 = st.columns(2)
with c1:
    p_achat_new = st.number_input("Prix d’achat principal", value=1.00000, step=0.00001, format="%.5f")
with c2:
    pct_profit_new = st.number_input("Profit (%) pour vendre 100%", value=3.0, step=0.1)

st.write("### 📊 Ajouter des paliers d’achat")

new_paliers = []
nb = st.number_input("Nombre de paliers", min_value=1, max_value=20, value=1)

for i in range(nb):
    c1, c2 = st.columns(2)
    with c1:
        p = st.number_input(f"Prix Palier {i+1}", value=1.00000, step=0.00001, format="%.5f", key=f"px{i}")
    with c2:
        m = st.number_input(f"Montant Palier {i+1} ($)", value=10.0, step=1.0, key=f"mx{i}")
    new_paliers.append({"prix": p, "montant": m})

if st.button("Créer le bot"):
    next_id = max(st.session_state.bots.keys()) + 1 if st.session_state.bots else 1

    st.session_state.bots[next_id] = {
        "id": next_id,
        "p_achat": p_achat_new,
        "pct_profit": pct_profit_new,
        "paliers": new_paliers,
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

    # Market precision
    try:
        market = exchange.market(symbol)
        qty_precision = int(market.get("precision", {}).get("amount", 4))
    except:
        qty_precision = 4

    # === ACHATS PAR PALIERS ===
    if b["etape"] == "ACHAT":

        for pal in b["paliers"]:
            prix_palier = pal["prix"]
            montant_palier = pal["montant"]

            if mid <= prix_palier and usdc >= montant_palier:
                if not verrou["trade_lock"]:
                    verrou["trade_lock"] = True
                    b["etape"] = "EN_COURS_ACHAT"
                    save_bots()

                    try:
                        qty = round(montant_palier / prix_palier, qty_precision)
                        exchange.create_limit_buy_order(symbol, qty, prix_palier)

                        b["investi"] += montant_palier
                        log(f"Bot {i} : Achat palier ({montant_palier}$) à {prix_palier}")
                        b["etape"] = "VENTE"

                    except Exception as e:
                        log(f"Bot {i} : erreur achat palier : {e}")
                        b["etape"] = "ACHAT"

                    verrou["trade_lock"] = False
                    save_bots()
                    break


    # === VENTE 100% DU XRP INVESTI ===
    prix_vente = b["p_achat"] * (1 + b["pct_profit"] / 100)

    if b["etape"] == "VENTE" and mid >= prix_vente:

        if not verrou["trade_lock"] and b["investi"] > 0:

            verrou["trade_lock"] = True
            b["etape"] = "EN_COURS_VENTE"
            save_bots()

            try:
                qty_sell = round(b["investi"] / b["p_achat"], qty_precision)
                exchange.create_limit_sell_order(symbol, qty_sell, prix_vente)

                gain = b["investi"] * (b["pct_profit"] / 100)

                b["gain_net"] += gain
                b["cycles"] += 1
                b["investi"] = 0
                b["etape"] = "ACHAT"

                log(f"Bot {i} : Vente 100% | Gain : {gain:.2f}$")

            except Exception as e:
                log(f"Bot {i} : erreur vente : {e}")
                b["etape"] = "VENTE"

            verrou["trade_lock"] = False
            save_bots()


# === GAIN GLOBAL ===
total_gain = sum(b["gain_net"] for b in st.session_state.bots.values())
st.success(f"💰 Gain total cumulé : {total_gain:.2f}$")
st.divider()


# === AFFICHAGE DES BOTS ===
st.subheader("📊 Liste des bots")

for i, b in sorted(st.session_state.bots.items()):

    col1, col2, col3 = st.columns([5, 1, 1])

    with col1:
        text = (
            f"Bot {i} | Profit {b['pct_profit']}% | Investi {b['investi']:.2f}$ | "
            f"Gain {b['gain_net']:.2f}$ | Cycles {b['cycles']} | Étape : {b['etape']}"
        )
        st.info(text)

        st.write("Paliers :")
        for p in b["paliers"]:
            st.write(f"- {p['prix']:.5f} → {p['montant']}$")

    # Toggle
    with col2:
        toggle = "🛑" if b["actif"] else "🚀"
        if st.button(toggle, key=f"toggle_{i}"):
            b["actif"] = not b["actif"]
            save_bots()
            st.rerun()

    # Delete
    with col3:
        if st.button("🗑️", key=f"del_{i}"):
            del st.session_state.bots[i]
            save_bots()
            st.rerun()


# === LOGS ===
st.divider()
st.subheader("📜 Journal des événements")
if st.session_state.logs:
    st.text_area("Logs", "\n".join(reversed(st.session_state.logs[-200:])), height=250)
