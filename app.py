import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIGURATION DE BASE
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro", layout="wide")
DB_FILE = "config_bots_xrp_secure.json"
symbol = "XRP/USDC"

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")
    if len(st.session_state.logs) > 20: st.session_state.logs.pop(0)

# ------------------------------------------------------------
# AUTO-REFRESH INTELLIGENT (S'arrête quand on tape)
# ------------------------------------------------------------
def auto_refresh():
    st.markdown("""
        <script>
            var timer = setTimeout(function() {
                // Ne rafraîchit PAS si l'utilisateur est en train de taper (input ou textarea)
                var activeElem = document.activeElement.tagName;
                if (activeElem !== 'INPUT' && activeElem !== 'TEXTAREA') {
                    window.parent.document.querySelectorAll('button').forEach(function(btn) {
                        if (btn.innerText === 'refresh_hidden') { btn.click(); }
                    });
                }
            }, 1500); // 1.5s pour laisser un peu d'air
        </script>
    """, unsafe_allow_html=True)
    st.button("refresh_hidden", key="refresh_button", help="Bouton caché")

auto_refresh()

# ------------------------------------------------------------
# SAUVEGARDE ET CHARGEMENT
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
# INITIALISATION DES BOTS
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

# ------------------------------------------------------------
# CONNEXION KRAKEN (SÉCURISÉE PAR SECRETS)
# ------------------------------------------------------------
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })

exchange = get_exchange()

# ------------------------------------------------------------
# MOTEUR DE TRADING (RUN_CYCLE)
# ------------------------------------------------------------
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
        
        # Calcul du changement de prix pour l'affichage
        old_p = st.session_state.get("price", price)
        st.session_state.diff = price - old_p
        st.session_state.price = price
        
        bal = exchange.fetch_balance()
        st.session_state.usdc = bal["free"].get("USDC", 0)
        st.session_state.xrp = bal["free"].get("XRP", 0)

        if not st.session_state.run: return

        for i, bot in st.session_state.bots.items():
            if not bot["actif"]: continue

            # LOGIQUE ACHAT
            if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
                if st.session_state.usdc >= bot["mise"]:
                    qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.985) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"], bot["etape"] = qty, "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                    log(f"✅ Bot {i} : ACHAT XRP à {price}")

            # LOGIQUE VENTE
            elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
                if bot["qty"] > 0:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.99))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    profit = ((price - bot["p_achat"]) * bot["qty"]) - (bot["mise"] * 0.006)
                    bot["gain_cumule"] += profit
                    bot["cycles"] += 1
                    bot["qty"], bot["etape"] = 0, "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"💰 Bot {i} : VENTE OK | Profit: {profit:.4f}")

    except Exception as e:
        if "Rate limit" not in str(e): # Évite de polluer les logs avec les limites Kraken
            log(f"⚠️ Erreur: {str(e)}")

run_cycle()

# ------------------------------------------------------------
# INTERFACE UTILISATEUR (UI)
# ------------------------------------------------------------
st.title("🚀 XRP Sniper Pro")

with st.sidebar:
    st.header("⚙️ CONFIGURATION")
    
    # Choix du bot avec Key unique
    id_bot = st.selectbox("Sélectionner Bot n°", range(1, 51), key="main_bot_select")
    bot_data = st.session_state.bots[id_bot]

    # Formulaire de saisie avec Keys uniques pour éviter les bugs de focus
    with st.form(key=f"form_bot_{id_bot}"):
        actif = st.checkbox("Activer ce bot", value=bot_data["actif"])
        p_achat = st.number_input("Prix Achat", value=float(bot_data["p_achat"]), format="%.4f")
        p_vente = st.number_input("Prix Vente", value=float(bot_data["p_vente"]), format="%.4f")
        mise = st.number_input("Mise (USDC)", value=float(bot_data["mise"]))
        
        submit = st.form_submit_button("💾 ENREGISTRER CONFIG")
        if submit:
            st.session_state.bots[id_bot].update({
                "actif": actif, "p_achat": p_achat, "p_vente": p_vente, "mise": mise
            })
            save_config(st.session_state.bots)
            st.success(f"Bot {id_bot} mis à jour !")

    st.divider()
    # Boutons de contrôle globaux
    col_start, col_stop = st.columns(2)
    if col_start.button("▶️ START", use_container_width=True): 
        st.session_state.run = True
        st.rerun()
    if col_stop.button("🛑 STOP", use_container_width=True): 
        st.session_state.run = False
        st.rerun()

# --- TABLEAU DE BORD (METRICS) ---
p = st.session_state.get("price", 0)
d = st.session_state.get("diff", 0)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Prix XRP", f"{p:.5f}", delta=f"{d:.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc', 0):.2f}")
m3.metric("Solde XRP", f"{st.session_state.get('xrp', 0):.2f}")
m4.metric("Gain Total", f"{sum(b['gain_cumule'] for b in st.session_state.bots.values()):.4f}")

st.divider()

# --- AFFICHAGE DES BOTS ACTIFS ---
st.subheader("🤖 Surveillance des Bots Actifs")
cols_ratio = [0.5, 1, 1, 1, 1, 1, 1]
h = st.columns(cols_ratio)
for col, text in zip(h, ["ID", "Statut", "Achat", "Vente", "Mise", "Cycles", "Gain"]):
    col.write(f"**{text}**")

for i, b in st.session_state.bots.items():
    if b["actif"]:
        r = st.columns(cols_ratio)
        r[0].write(str(i))
        r[1].write("🔵 VENTE" if b["etape"] == "ATTENTE_VENTE" else "🟢 ACHAT")
        r[2].write(f"{b['p_achat']:.4f}")
        r[3].write(f"{b['p_vente']:.4f}")
        r[4].write(f"{b['mise']:.2f}")
        r[5].write(str(b['cycles']))
        r[6].write(f"{b['gain_cumule']:.4f}")

# --- LOGS ---
st.divider()
st.subheader("📜 Journal d'activité")
st.code("\n".join(st.session_state.logs[::-1]))
