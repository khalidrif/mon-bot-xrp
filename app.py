import streamlit as st
import ccxt
import time
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP 50 Bots Sauvegardés", layout="wide")
DB_FILE = "bots_config.json"  # Fichier de sauvegarde

# --- FONCTIONS DE SAUVEGARDE ---
def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            # On convertit les clés en entiers car JSON les transforme en texte
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return None

# --- INITIALISATION ---
if 'bots' not in st.session_state:
    saved = load_data()
    if saved:
        st.session_state.bots = saved
        st.success("✅ Réglages chargés depuis le fichier !")
    else:
        st.session_state.bots = {i: {"p_achat": 1.35, "p_vente": 1.38, "mise": 10.0, "etape": "ATTENTE_ACHAT", "actif": False} for i in range(1, 51)}

# --- CONNEXION KRAKEN ---
@st.cache_resource
def get_exchange():
    ex = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_API_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': 'milliseconds'}
    })
    ex.load_markets()
    return ex

exchange = get_exchange()
symbol = "XRP/USDC"

# --- SIDEBAR (SAISIE & SAUVEGARDE) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    choix_bot = st.selectbox("Modifier Bot n°", range(1, 51))
    
    with st.container(border=True):
        bot = st.session_state.bots[choix_bot]
        bot["actif"] = st.toggle("Activer", value=bot["actif"], key=f"tgl_{choix_bot}")
        bot["p_achat"] = st.number_input("Prix ACHAT", value=bot["p_achat"], format="%.4f", key=f"ac_{choix_bot}")
        bot["p_vente"] = st.number_input("Prix VENTE", value=bot["p_vente"], format="%.4f", key=f"ve_{choix_bot}")
        bot["mise"] = st.number_input("Mise USDC", value=bot["mise"], key=f"mi_{choix_bot}")
        
        if st.button("💾 SAUVEGARDER TOUT", use_container_width=True):
            save_data(st.session_state.bots)
            st.toast("Configuration enregistrée !")

    st.divider()
    if st.button("🚀 DÉMARRER", type="primary", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP", use_container_width=True): st.session_state.run = False

# --- AFFICHAGE & LOGIQUE (CENTRE) ---
st.title("🛰️ Multi-Bots XRP (Mémoire Longue)")

try:
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['last']
    st.metric("Prix XRP Actuel", f"{price:.4f} USDC")
    
    # Affichage des bots actifs
    for i, b in st.session_state.bots.items():
        if b["actif"]:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.write(f"**Bot #{i}**")
                c2.write(f"État: **{b['etape']}**")
                c3.write(f"Cibles: {b['p_achat']} ➔ {b['p_vente']}")
                # On sauvegarde l'état à chaque changement d'étape (achat/vente)
                if b["etape"] == "ATTENTE_ACHAT" and price <= b["p_achat"]:
                    # ... LOGIQUE ACHAT ... (comme avant)
                    b["etape"] = "ATTENTE_VENTE"
                    save_data(st.session_state.bots) # Sauvegarde immédiate du changement
                    st.rerun()
                elif b["etape"] == "ATTENTE_VENTE" and price >= b["p_vente"]:
                    # ... LOGIQUE VENTE ... (comme avant)
                    b["etape"] = "ATTENTE_ACHAT"
                    save_data(st.session_state.bots) # Sauvegarde immédiate du changement
                    st.rerun()
except Exception as e:
    st.error(f"Erreur: {e}")

time.sleep(20)
st.rerun()
