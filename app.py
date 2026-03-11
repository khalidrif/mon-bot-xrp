import streamlit as st
import ccxt
import json
import os
import time
from streamlit_autorefresh import st_autorefresh

# === CONFIGURATION ===
st.set_page_config(page_title="⚡ XRP Sniper Pro - Gains & Boule de neige", layout="centered")
symbol = "XRP/USDC"
st_autorefresh(interval=20000, key="refresh_app")
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

# === CONNEXION KRAKEN ===
@st.cache_resource
def get_exchange():
    try:
        return ccxt.kraken({
            "apiKey": st.secrets["KRAKEN_API_KEY"],
            "secret": st.secrets["KRAKEN_API_SECRET"],
            "enableRateLimit": True
        })
    except Exception as e:
        log(f"⚠️ Kraken : {e}")
        return None

exchange = get_exchange()

# === INIT DES BOTS ===
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

# === PRIX LIVE ===
try:
    ticker = exchange.fetch_ticker(symbol)
    bid = ticker["bid"]
    ask = ticker["ask"]
    mid = (bid + ask) / 2
    log(f"📡 Prix reçu : Bid {bid:.5f} – Ask {ask:.5f}")
except Exception as e:
    bid = ask = mid = 0.0
    log(f"⚠️ Erreur récupération ticker : {e}")

# === INTERFACE ===
st.title("🚀 XRP Sniper Simple - Gains & Boule de neige")
st.metric("Prix XRP", f"{mid:.5f}")
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

if st.button("✅ Créer Bot"):
    next_id = max(st.session_state.bots.keys()) + 1 if st.session_state.bots else 1
    st.session_state.bots[next_id] = {
        "id": next_id,
        "p_achat": p_achat_new,
        "p_vente": p_vente_new,
        "mise": mise_new,
        "gain_net": 0.0,
        "cycles": 0,
        "actif": True,
        "etape": "ACHAT"
    }
    save_bots()
    log(f"🆕 Bot #{next_id} ajouté (Achat {p_achat_new:.4f} / Vente {p_vente_new:.4f})")
    st.success(f"Bot #{next_id} créé 🎯")
    st.rerun()

# === LOGIQUE SIMULÉE (Boule de neige + cycles + gains) ===
# 👉 Simulation simple : quand prix <= achat => étape VENTE
#    puis quand prix >= vente => gain + cycle + mise += gain
for i, b in st.session_state.bots.items():
    if not b.get("actif", True):
        continue

    # ACHAT
    if b["etape"] == "ACHAT" and mid <= b["p_achat"]:
        b["etape"] = "VENTE"
        log(f"🟡 Bot #{i} : condition d'achat atteinte ({mid:.5f})")

    # VENTE
    elif b["etape"] == "VENTE" and mid >= b["p_vente"]:
        gain = (b["p_vente"] - b["p_achat"]) / b["p_achat"] * b["mise"]
        b["gain_net"] += gain
        b["cycles"] += 1
        b["mise"] += gain  # effet boule de neige
        b["etape"] = "ACHAT"  # repart pour un cycle
        log(f"💰 Bot #{i} : +{gain:.2f}$ gain cycle {b['cycles']} (nouvelle mise {b['mise']:.2f}$)")
        save_bots()

# === LISTE DES BOTS ===
st.divider()
st.subheader("📊 Mes Bots")

if not st.session_state.bots:
    st.info("Aucun bot actif.")
else:
    for i, b in sorted(st.session_state.bots.items()):
        actif = b.get("actif", True)
        couleur, zone = ("⚫️", "Inactif") if not actif else ("🟢", "Observation")
        if actif:
            if mid <= b["p_achat"]:
                couleur, zone = ("🟡", "Achat possible")
            elif mid >= b["p_vente"]:
                couleur, zone = ("🔴", "Vente possible")

        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.info(
                f"{couleur} **Bot {i}** → Achat {b['p_achat']:.4f} | Vente {b['p_vente']:.4f} | "
                f"Mise : {b['mise']:.2f}$ | Gain : {b['gain_net']:.2f}$ | Cycles : {b['cycles']}"
            )
        with col2:
            # Activer / Désactiver
            toggle = "🛑" if actif else "🚀"
            if st.button(toggle, key=f"toggle_{i}"):
                b["actif"] = not actif
                save_bots()
                log(f"🔁 Bot #{i} {'désactivé' if actif else 'activé'}.")
                st.rerun()
        with col3:
            # Supprimer
            if st.button("🗑️", key=f"del_{i}"):
                del st.session_state.bots[i]
                save_bots()
                log(f"🗑️ Bot #{i} supprimé.")
                st.rerun()
        with col4:
            st.write(zone)

# === LOGS ===
st.divider()
st.subheader("📜 Historique")
for msg in reversed(st.session_state.logs[-12:]):
    st.write(msg)

# === PRIX DÉTAILLÉ ===
st.divider()
st.subheader("💹 Prix temps réel")
colA, colB, colC = st.columns(3)
colA.metric("Bid", f"{bid:.5f}")
colB.metric("Ask", f"{ask:.5f}")
colC.metric("Mid", f"{mid:.5f}")
