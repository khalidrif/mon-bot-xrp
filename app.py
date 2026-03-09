import streamlit as st
import ccxt
import time
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Multi-Grid 50", layout="wide")

DB_FILE = "config_bots_xrp.json"

# --- FONCTIONS DE SAUVEGARDE (IMMORTALITÉ) ---
def save_config(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def load_config():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return None

# --- INITIALISATION DES 50 BOTS ---
if 'bots' not in st.session_state:
    saved = load_config()
    if saved:
        st.session_state.bots = saved
    else:
        st.session_state.bots = {i: {"p_achat": 1.35, "p_vente": 1.38, "mise": 10.0, "etape": "ATTENTE_ACHAT", "actif": False} for i in range(1, 51)}

if 'run' not in st.session_state: st.session_state.run = False

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

# --- BARRE LATÉRALE (SAISIE GAUCHE) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    id_bot = st.selectbox("Sélectionner Bot n°", range(1, 51))
    
    with st.container(border=True):
        b_cfg = st.session_state.bots[id_bot]
        b_cfg["actif"] = st.toggle("Activer ce bot", value=b_cfg["actif"], key=f"tgl_{id_bot}")
        b_cfg["p_achat"] = st.number_input("Prix ACHAT", value=b_cfg["p_achat"], format="%.4f", key=f"ac_{id_bot}")
        b_cfg["p_vente"] = st.number_input("Prix VENTE", value=b_cfg["p_vente"], format="%.4f", key=f"ve_{id_bot}")
        b_cfg["mise"] = st.number_input("Mise USDC", value=b_cfg["mise"], key=f"mi_{id_bot}")
        
        if st.button("💾 SAUVEGARDER RÉGLAGES", use_container_width=True):
            save_config(st.session_state.bots)
            st.toast("Configuration enregistrée !")

    st.divider()
    if st.button("🚀 DÉMARRER TOUT", type="primary", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False

# --- AFFICHAGE CENTRAL ---
st.title("🛰️ Dashboard Multi-Bots XRP")

try:
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['last']
    bal = exchange.fetch_balance()
    usdc_bal = bal['free'].get('USDC', 0.0)
    
    col_p, col_b = st.columns(2)
    col_p.metric("Prix XRP Actuel", f"{price:.4f} USDC")
    col_b.metric("Solde USDC Libre", f"{usdc_bal:.2f}")

    st.divider()

    # --- HEADER DU TABLEAU ---
    h1, h2, h3, h4, h5, h6 = st.columns([0.5, 1, 1, 1, 1, 1])
    h1.write("**N°**")
    h2.write("**État**")
    h3.write("**Cible Achat**")
    h4.write("**Cible Vente**")
    h5.write("**Mise**")
    h6.write("**Statut**")

    # --- LIGNES DES BOTS ---
    for i, bot in st.session_state.bots.items():
        if bot["actif"]:
            with st.container(border=True):
                c1, c2, c3, c4, c5, c6 = st.columns([0.5, 1, 1, 1, 1, 1])
                c1.write(f"#{i}")
                
                # Colonne État
                if bot["etape"] == "ATTENTE_ACHAT":
                    c2.warning("⏳ ACHAT")
                else:
                    c2.success("💰 VENTE")
                
                c3.write(f"{bot['p_achat']:.4f}")
                c4.write(f"{bot['p_vente']:.4f}")
                c5.write(f"{bot['mise']} $")
                
                # Colonne Statut (Distance)
                dist = abs(price - (bot['p_achat'] if bot['etape'] == "ATTENTE_ACHAT" else bot['p_vente']))
                c6.write("🎯 Proche" if dist < 0.005 else "---")

                # --- LOGIQUE DE TRADING ---
                if st.session_state.run:
                    # ACHAT
                    if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                        if usdc_bal >= bot["mise"]:
                            q = float(exchange.amount_to_precision(symbol, bot["mise"] / bot["p_achat"]))
                            p = float(exchange.price_to_precision(symbol, bot["p_achat"]))
                            exchange.create_limit_buy_order(symbol, q, p)
                            bot["etape"] = "ATTENTE_VENTE"
                            save_config(st.session_state.bots) # Sauvegarde le changement d'état
                            st.rerun()
                    # VENTE
                    elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                        # Calcul quantité basée sur l'achat estimé
                        q_v = float(exchange.amount_to_precision(symbol, (bot["mise"] / bot["p_achat"]) * 0.995))
                        p_v = float(exchange.price_to_precision(symbol, bot["p_vente"]))
                        exchange.create_limit_sell_order(symbol, q_v, p_v)
                        bot["etape"] = "ATTENTE_ACHAT"
                        save_config(st.session_state.bots) # Sauvegarde le retour à l'achat
                        st.balloons()
                        st.rerun()

except Exception as e:
    st.error(f"Erreur API : {e}")

time.sleep(20)
st.rerun()
