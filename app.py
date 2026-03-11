import streamlit as st
import ccxt
import json
import os
import time
from streamlit_autorefresh import st_autorefresh

# === CONFIGURATION ===
st.set_page_config(page_title="⚡ XRP Sniper Simple", layout="centered")
symbol = "XRP/USDC"
st_autorefresh(interval=30000, key="refresh_app")
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
        log(f"⚠️ Erreur Kraken : {e}")
        return None

exchange = get_exchange()

# === INIT DES BOTS ===
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

# === PRIX MARCHÉ XRP ===
try:
    ticker = exchange.fetch_ticker(symbol)
    price = (ticker["bid"] + ticker["ask"]) / 2
except Exception:
    price = 0.0

# === INTERFACE ===
st.title("🚀 XRP Sniper Simple (Activable)")
st.metric("Prix XRP actuel", f"{price:.5f}")
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

if st.button("✅ Ajouter ce bot"):
    next_id = max(st.session_state.bots.keys()) + 1 if st.session_state.bots else 1
    st.session_state.bots[next_id] = {
        "id": next_id,
        "p_achat": p_achat_new,
        "p_vente": p_vente_new,
        "mise": mise_new,
        "etat": "ATTENTE",
        "actif": True,  # ACTIVE PAR DÉFAUT
        "gain": 0.0
    }
    save_bots()
    log(f"➕ Bot #{next_id} ajouté (Achat {p_achat_new}, Vente {p_vente_new})")
    st.success(f"Bot #{next_id} créé 🎯")
    st.rerun()

# === LISTE DES BOTS ===
st.divider()
st.subheader("📊 Mes bots")

if not st.session_state.bots:
    st.info("Aucun bot enregistré.")
else:
    for i, b in sorted(st.session_state.bots.items()):
        # Couleur selon prix et état actif/inactif
        couleur = "⚫️" if not b.get("actif", True) else "🟢"
        message = "Inactif" if not b.get("actif", True) else "Actif"

        if b.get("actif", True):
            if price <= b["p_achat"]:
                couleur = "🟡"
                message = "Zone d'achat"
            elif price >= b["p_vente"]:
                couleur = "🔴"
                message = "Zone de vente"

        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.info(
                f"{couleur} **Bot {i}** → Achat : {b['p_achat']:.4f} | "
                f"Vente : {b['p_vente']:.4f} | Mise : {b['mise']:.2f}$ | {message}"
            )
        with col2:
            # Bouton activer/désactiver
            label = "🛑" if b.get("actif", True) else "🚀"
            if st.button(label, key=f"toggle_{i}"):
                b["actif"] = not b.get("actif", True)
                save_bots()
                st.rerun()
        with col3:
            # Bouton supprimer
            if st.button("🗑️", key=f"del_{i}"):
                del st.session_state.bots[i]
                save_bots()
                st.warning(f"Bot #{i} supprimé")
                st.rerun()

# === LOGS ===
st.divider()
for m in reversed(st.session_state.logs[-8:]):
    st.write(m)
