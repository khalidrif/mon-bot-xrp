# app.py
import streamlit as st
import datetime
import json
import os
from typing import Dict

# ---------- Configuration ----------
NUM_BOTS = 50
DATA_FILE = "bots_config.json"

# ---------- Helpers ----------
def load_config() -> Dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(bots: Dict):
    try:
        # sauvegarde atomique: écrire dans fichier temporaire puis renommer
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(bots, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)
        st.toast("Configuration sauvegardée ✔")
    except Exception as e:
        st.error(f"Erreur sauvegarde: {e}")

def reset_bot(id_bot: int):
    default = {"actif": False, "p_achat": 0.0, "p_vente": 0.0, "mise": 0.0}
    st.session_state.bots[str(id_bot)] = default
    save_config(st.session_state.bots)
    st.toast(f"Bot {id_bot} réinitialisé ✔")

# ---------- Init session_state ----------
if "session_uid" not in st.session_state:
    st.session_state.session_uid = str(int(datetime.datetime.now().timestamp()))
if "bots" not in st.session_state:
    # try load saved config, else create defaults
    loaded = load_config()
    if loaded:
        st.session_state.bots = {k: v for k, v in loaded.items()}
    else:
        st.session_state.bots = {
            str(i): {"actif": False, "p_achat": 0.0, "p_vente": 0.0, "mise": 0.0}
            for i in range(1, NUM_BOTS + 1)
        }
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "run" not in st.session_state:
    st.session_state.run = False
if "stop_clicked" not in st.session_state:
    st.session_state.stop_clicked = False
if "trade_count" not in st.session_state:
    st.session_state.trade_count = 0
if "start_capital" not in st.session_state:
    st.session_state.start_capital = 0.0

# ---------- UI ----------
st.title("Gestion des bots")

# Sélection du bot
id_bot = st.selectbox(
    "Bot n°",
    list(range(1, NUM_BOTS + 1)),
    key=f"bot_select_sidebar_{st.session_state.session_uid}"
)
bot_key = str(id_bot)
bot = st.session_state.bots.get(bot_key, {"actif": False, "p_achat": 0.0, "p_vente": 0.0, "mise": 0.0})

# Activation du bot
bot["actif"] = st.toggle(
    "Activer",
    bot["actif"],
    key=f"actif_{id_bot}_{st.session_state.session_uid}"
)

# Paramètres du bot
bot["p_achat"] = st.number_input(
    "Prix Achat",
    value=float(bot.get("p_achat", 0.0)),
    format="%.4f",
    key=f"p_achat_{id_bot}_{st.session_state.session_uid}"
)
bot["p_vente"] = st.number_input(
    "Prix Vente",
    value=float(bot.get("p_vente", 0.0)),
    format="%.4f",
    key=f"p_vente_{id_bot}_{st.session_state.session_uid}"
)
bot["mise"] = st.number_input(
    "Mise (USDC)",
    value=float(bot.get("mise", 0.0)),
    format="%.4f",
    key=f"mise_{id_bot}_{st.session_state.session_uid}"
)

# write back changes to session_state
st.session_state.bots[bot_key] = bot

st.divider()

# Boutons Sauvegarder / Réinitialiser
if st.button("💾 Sauvegarder", key=f"save_{id_bot}_{st.session_state.session_uid}"):
    save_config(st.session_state.bots)

if st.button("🗑 Réinitialiser le bot", key=f"reset_{id_bot}_{st.session_state.session_uid}"):
    # confirmation simple
    if st.confirm(f"Confirmer la réinitialisation du bot {id_bot} ?"):
        reset_bot(id_bot)

st.divider()

# Démarrer / Stop
def start_bots():
    if st.session_state.run:
        st.toast("Les bots sont déjà démarrés")
        return
    st.session_state.run = True
    st.session_state.stop_clicked = False
    if st.session_state.start_time is None:
        st.session_state.start_time = datetime.datetime.now()
        st.session_state.trade_count = 0
        # safe sum using get/default
        st.session_state.start_capital = sum(
            float(b.get("mise", 0.0)) for b in st.session_state.bots.values()
        )
    st.toast("Bots démarrés 🚀")

def stop_bots():
    st.session_state.run = False
    st.session_state.stop_clicked = True
    st.toast("Bots arrêtés 🛑")

col1, col2 = st.columns(2)
with col1:
    st.button("🚀 Démarrer", on_click=start_bots, key=f"start_{st.session_state.session_uid}")
with col2:
    st.button("🛑 Stop", on_click=stop_bots, key=f"stop_{st.session_state.session_uid}")

# Affichage d'état simple
st.markdown(f"- Run: {st.session_state.run}")
st.markdown(f"- Start time: {st.session_state.start_time}")
st.markdown(f"- Start capital: {st.session_state.start_capital:.4f}")
st.markdown(f"- Nombre de bots configurés: {len(st.session_state.bots)}")
