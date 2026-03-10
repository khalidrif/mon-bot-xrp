import streamlit as st
import ccxt
import time
import json
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="XRP Sniper Pro 50", layout="wide")
DB_FILE = "config_bots_xrp_final.json"

# --- FONCTIONS DE SAUVEGARDE (IMMORTALITÉ) ---
def save_config(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def load_config():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except: return None
    return None

# --- INITIALISATION ---
if 'bots' not in st.session_state:
    saved = load_config()
    if saved:
        st.session_state.bots = saved
    else:
        st.session_state.bots = {i: {"p_achat": 1.35, "p_vente": 1.38, "mise": 10.0, "etape": "ATTENTE_ACHAT", "actif": False, "cycles": 0, "gain_cumule": 0.0} for i in range(1, 51)}

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

# --- SIDEBAR (SAISIE À GAUCHE) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    id_bot = st.selectbox("Sélectionner Bot n°", range(1, 51))
    
    with st.container(border=True):
        b_cfg = st.session_state.bots[id_bot]
        b_cfg["actif"] = st.toggle("Activer ce bot", value=b_cfg["actif"], key=f"tgl_{id_bot}")
        b_cfg["p_achat"] = st.number_input("Prix ACHAT", value=b_cfg["p_achat"], format="%.4f", key=f"ac_{id_bot}")
        b_cfg["p_vente"] = st.number_input("Prix VENTE", value=b_cfg["p_vente"], format="%.4f", key=f"ve_{id_bot}")
        b_cfg["mise"] = st.number_input("Mise USDC", value=b_cfg["mise"], key=f"mi_{id_bot}")
        
        if st.button("💾 SAUVEGARDER", use_container_width=True):
            save_config(st.session_state.bots)
            st.toast("Configuration enregistrée !")

    st.divider()
    if st.button("🚀 DÉMARRER TOUT", type="primary", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False

# --- DASHBOARD CENTRAL ---
st.title("🎯 XRP Sniper Pro 50")

try:
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['last']
    bal = exchange.fetch_balance()
    usdc_bal = bal['free'].get('USDC', 0.0)
    xrp_bal_total = bal['free'].get('XRP', 0.0)
    
    total_gains = sum(b.get('gain_cumule', 0.0) for b in st.session_state.bots.values())
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Prix XRP Actuel", f"{price:.4f} USDC")
    m2.metric("Solde USDC Libre", f"{usdc_bal:.2f} $")
    m3.metric("Gain Total Net", f"{total_gains:.2f} $", delta=f"{total_gains:.4f}")

    st.divider()

    # --- TABLEAU DES BOTS (CORRECTIF ICI) ---
    cols_size = [0.5, 1.2, 1, 1, 0.8, 0.6, 1, 0.8]
    h = st.columns(cols_size)
    headers = ["N°", "État", "Achat", "Vente", "Mise", "Cyc.", "Gain Net", "Act."]
    
    # On écrit chaque titre dans sa colonne respective
    for col, text in zip(h, headers):
        col.write(f"**{text}**")

    for i, bot in st.session_state.bots.items():
        if bot["actif"]:
            with st.container(border=True):
                c = st.columns(cols_size)
                c.write(f"#{i}")
                
                if bot["etape"] == "ATTENTE_ACHAT":
                    c.warning("⏳ ACHAT")
                else:
                    c.success("💰 VENTE")
                
                c.write(f"{bot['p_achat']:.4f}")
                c.write(f"{bot['p_vente']:.4f}")
                c.write(f"{bot['mise']}$")
                c.write(f"{bot.get('cycles', 0)}")
                c.write(f"**{bot.get('gain_cumule', 0.0):.3f}$**")
                
                # Bouton de suppression sur la ligne
                if c[7].button("🗑️", key=f"del_{i}"):
                    st.session_state.bots[i] = {"p_achat": 1.35, "p_vente": 1.38, "mise": 10.0, "etape": "ATTENTE_ACHAT", "actif": False, "cycles": 0, "gain_cumule": 0.0}
                    save_config(st.session_state.bots)
                    st.rerun()

                # --- LOGIQUE DE TRADING ---
                if st.session_state.run:
                    # 1. ACHAT AU MARCHÉ
                    if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                        if usdc_bal >= bot["mise"]:
                            q = float(exchange.amount_to_precision(symbol, bot["mise"] / price))
                            exchange.create_market_buy_order(symbol, q)
                            bot["etape"] = "ATTENTE_VENTE"
                            save_config(st.session_state.bots)
                            st.rerun()
                    # 2. VENTE AU MARCHÉ
                    elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                        if xrp_bal_total > 1:
                            q_v = float(exchange.amount_to_precision(symbol, (bot["mise"] / bot["p_achat"]) * 0.99))
                            exchange.create_market_sell_order(symbol, q_v)
                            # Calcul Gain (Frais 0.6% estimés)
                            gain_net = ((bot["p_vente"] - bot["p_achat"]) * (bot["mise"] / bot["p_achat"])) - (bot["mise"] * 0.006)
                            bot["etape"] = "ATTENTE_ACHAT"
                            bot["cycles"] = bot.get("cycles", 0) + 1
                            bot["gain_cumule"] = bot.get("gain_cumule", 0.0) + gain_net
                            save_config(st.session_state.bots)
                            st.balloons()
                            st.rerun()

except Exception as e:
    st.error(f"Erreur : {e}")

time.sleep(15)
st.rerun()
