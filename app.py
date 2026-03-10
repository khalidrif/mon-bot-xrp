import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro", layout="wide")
DB_FILE = "config_bots_xrp_secure.json"
symbol = "XRP/USDC"

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# ------------------------------------------------------------
# AUTO-REFRESH
# ------------------------------------------------------------
def auto_refresh():
    st.markdown("""
        <script>
            setTimeout(function() {
                document.getElementById('refresh_button').click();
            }, 800);
        </script>
    """, unsafe_allow_html=True)
    st.button("refresh", key="refresh_button")
auto_refresh()

if "run" not in st.session_state:
    st.session_state.run = False

if "trades" not in st.session_state:
    st.session_state.trades = []

def save_trades_json():
    with open("trades_log.json", "w") as f:
        json.dump(st.session_state.trades, f, indent=2)

def save_trades_csv():
    with open("trades_log.csv", "w") as f:
        f.write("time,bot,type,qty,price,gain\n")
        for t in st.session_state.trades:
            f.write(",".join(str(x) for x in t.values()) + "\n")

def save_config(bots):
    try:
        with open("backup_config.json", "w") as bkp:
            json.dump(bots, bkp)
    except:
        pass
    if not isinstance(bots, dict) or len(bots) == 0:
        st.error("🔥 Tentative d'écraser avec fichier vide BLOQUÉE !")
        return
    try:
        with open(DB_FILE, "w") as f:
            json.dump(bots, f)
    except Exception as e:
        st.error(f"❌ ERREUR SAUVEGARDE : {e}")

def load_config():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict) or len(data) == 0:
                raise ValueError("Config vide/corrompue")
            return {int(k): v for k, v in data.items()}
        except:
            st.warning("⚠️ Config corrompue → restauration backup…")
            if os.path.exists("backup_config.json"):
                with open("backup_config.json", "r") as f:
                    backup = json.load(f)
                st.success("✨ Backup restauré")
                return {int(k): v for k, v in backup.items()}
            else:
                st.error("❌ Aucun backup trouvé")
                return None
    return None

def reset_bot(i):
    st.session_state.bots[i] = {
        "actif": False,
        "p_achat": 1.35,
        "p_vente": 1.38,
        "mise": 15.0,
        "etape": "ATTENTE_ACHAT",
        "qty": 0.0,
        "cycles": 0,
        "gain_cumule": 0.0,
        "order_id": None
    }
    save_config(st.session_state.bots)
    log(f"Bot #{i} réinitialisé")

if "bots" not in st.session_state:
    cfg = load_config()
    if cfg:
        st.session_state.bots = cfg
    else:
        st.session_state.bots = {
            i: {
                "actif": False,
                "p_achat": 1.35,
                "p_vente": 1.38,
                "mise": 15.0,
                "etape": "ATTENTE_ACHAT",
                "qty": 0.0,
                "cycles": 0,
                "gain_cumule": 0.0,
                "order_id": None
            }
            for i in range(1, 51)
        }
        save_config(st.session_state.bots)

for bot in st.session_state.bots.values():
    if "order_id" not in bot:
        bot["order_id"] = None

@st.cache_resource
def get_exchange():
    ex = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
    ex.load_markets()
    return ex

exchange = get_exchange()

st.title("✅ Bloc 1 chargé – Config OK")
st.write("Passe à la suite : Bloc 2 / 3 (logique du bot)")
