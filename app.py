import streamlit as st
import ccxt
import json
import os
import time
from streamlit_autorefresh import st_autorefresh

# === CONFIGURATION ===
st.set_page_config(page_title="⚡ XRP Sniper Simple (Final)", layout="centered")
symbol = "XRP/USDC"
st_autorefresh(interval=20000, key="refresh_app")  # refresh 20 s
CONFIG_FILE = "bots_config.json"

# === SESSION / LOGS ===
if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# === SAUVEGARDE / CHARGEMENT ===
def save_bots():
    with open(CONFIG_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=2)

def load_bots():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}

# === KRAKEN ===
@st.cache_resource
def get_exchange():
    try:
        return ccxt.kraken({
            "apiKey": st.secrets["KRAKEN_API_KEY"],
            "secret": st.secrets["KRAKEN_API_SECRET"],
            "enableRateLimit": True
        })
    except Exception as e:
        log(f"⚠️ Erreur Kraken : {e}")
        return None

exchange = get_exchange()

# === INIT BOTS ===
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

# === RÉCUPÉRATION PRIX LIVE ===
try:
    ticker = exchange.fetch_ticker(symbol)
    price_bid = ticker["bid"]
    price_ask = ticker["ask"]
    price_mid = (price_bid + price_ask) / 2
    log(f"📡 Prix reçu : Bid {price_bid:.5f} – Ask {price_ask:.5f}")
except Exception as e:
    price_bid = price_ask = price_mid = 0.0
    log(f"⚠️ Erreur récupération prix : {e}")

# === INTERFACE ===
st.title("🚀 XRP Sniper Simple (Version Finale)")
st.metric("💰 Prix XRP actuel", f"{price_mid:.5f}")
st.caption(f"Dernière mise à jour : {time.strftime('%H:%M:%S')}")
st.divider()

# === AJOUT D’UN BOT ===
st.subheader("➕ Ajouter un bot")

col1, col2, col3 = st.columns(3)
with col1:
    p_achat_new = st.number_input("Prix Achat", value=1.400, step=0.0001)
with col2:
    p_vente_new = st.number_input("Prix Vente", value=1.410, step=0.0001)
with col3:
    mise_new = st.number_input("Mise ($)", value=10.0, step=1.0)

if st.button("✅ Créer Bot"):
    next_id = max(st.session_state.bots.keys()) + 1 if st.session_state.bots else 1
    st.session_state.bots[next_id] = {
        "id": next_id,
        "p_achat": p_achat_new,
        "p_vente": p_vente_new,
        "mise": mise_new,
        "gain": 0.0,
        "etat": "ATTENTE",
        "actif": True
    }
    save_bots()
    log(f"🆕 Bot #{next_id} ajouté : Achat {p_achat_new} / Vente {p_vente_new}")
    st.success(f"Bot #{next_id} créé 🎯")
    st.rerun()

# === LISTE DES BOTS ===
st.divider()
st.subheader("📊 Mes bots")

if not st.session_state.bots:
    st.info("Aucun bot enregistré.")
else:
    for i, b in sorted(st.session_state.bots.items()):
        actif = b.get("actif", True)
        couleur, message = "⚫️", "Inactif"

        if actif:
            if price_mid <= b["p_achat"]:
                couleur, message = "🟡", "Zone d'achat"
            elif price_mid >= b["p_vente"]:
                couleur, message = "🔴", "Zone de vente"
            else:
                couleur, message = "🟢", "Actif et en observation"

        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.info(
                f"{couleur} **Bot {i}** → Achat : {b['p_achat']:.4f} | "
                f"Vente : {b['p_vente']:.4f} | Mise : {b['mise']:.2f}$ | {message}"
            )
        with col2:
            toggle_label = "🛑" if actif else "🚀"
            if st.button(toggle_label, key=f"toggle_{i}"):
                st.session_state.bots[i]["actif"] = not actif
                save_bots()
                state = "activé" if not actif else "désactivé"
                log(f"🔁 Bot #{i} {state}.")
                st.rerun()
        with col3:
            if st.button("🗑️", key=f"del_{i}"):
                del st.session_state.bots[i]
                save_bots()
                log(f"🗑️ Bot #{i} supprimé.")
                st.rerun()

# === LOGS ===
st.divider()
st.subheader("📜 Historique des tâches récentes")
for msg in reversed(st.session_state.logs[-10:]):
    st.write(msg)

# === PRIX EN DIRECT (BID / ASK / MID) ===
st.divider()
st.subheader("💹 Détail du Prix en temps réel")
colA, colB, colC = st.columns(3)
colA.metric("Bid (acheteurs)", f"{price_bid:.5f}")
colB.metric("Ask (vendeurs)", f"{price_ask:.5f}")
colC.metric("Prix moyen (Mid)", f"{price_mid:.5f}")
