import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION
st.set_page_config(page_title="XRP SNIPER FINAL", layout="wide")
symbol = "XRP/USDC"

# Connexion Sheets avec gestion d'erreur
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Erreur de connexion Sheets : {e}")

st_autorefresh(interval=40000, key="bot_refresh")

if "logs" not in st.session_state: st.session_state.logs = []
if "run" not in st.session_state: st.session_state.run = False

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# 2. KRAKEN
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
exchange = get_exchange()

# 3. SAUVEGARDE & CHARGEMENT
def load_config():
    try:
        df = conn.read(ttl=0)
        if df.empty: return {}
        # Nettoyage des données pour éviter les erreurs de type
        df = df.dropna(subset=['id'])
        bots = {}
        for _, row in df.iterrows():
            idx = int(row['id'])
            bots[idx] = row.to_dict()
        return bots
    except:
        return {}

def save_config(bots_dict):
    try:
        df_to_save = pd.DataFrame(list(bots_dict.values()))
        # Nettoyage avant envoi
        df_to_save['id'] = df_to_save['id'].astype(int)
        conn.update(data=df_to_save)
        st.success("💾 SYNCHRONISÉ !")
    except Exception as e:
        st.error(f"❌ ERREUR : {e}")

# 4. INITIALISATION
if "bots" not in st.session_state or not st.session_state.bots:
    st.session_state.bots = load_config()

# 5. LOGIQUE
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = (ticker["bid"] + ticker["ask"]) / 2
        st.session_state.price = price
        log(f"🎯 Prix : {price:.5f}")
    except:
        price = st.session_state.get("price", 0)

    if not st.session_state.run: return

    # Logique simplifiée pour éviter les blocages
    for i, bot in st.session_state.bots.items():
        if not bot.get("actif"): continue
        # Ton code d'achat/vente ici (le verrou pending_orders peut être rajouté après)

run_cycle()

# 6. INTERFACE
st.title("🚀 SNIPER PRO")

with st.sidebar:
    st.header("⚙️ Config")
    id_bot = st.number_input("Bot ID", min_value=1, max_value=50, value=1)
    
    # On récupère le bot ou on en crée un par défaut
    b = st.session_state.bots.get(id_bot, {"id": id_bot, "actif": False, "p_achat": 1.35, "p_vente": 1.38, "mise": 15.0, "etape": "ATTENTE_ACHAT", "gain_cumule": 0, "qty": 0})
    
    p_a = st.number_input("Achat", value=float(b["p_achat"]), format="%.4f")
    p_v = st.number_input("Vente", value=float(b["p_vente"]), format="%.4f")
    p_m = st.number_input("Mise", value=float(b["mise"]))
    
    if st.button("💾 ENREGISTRER"):
        b.update({"p_achat": p_a, "p_vente": p_v, "mise": p_m})
        st.session_state.bots[id_bot] = b
        save_config(st.session_state.bots)
        st.rerun()

# 7. TABLEAU SIMPLE (SANS INDEX COMPLEXES POUR ÉVITER LES ERREURS)
st.subheader("📊 Liste des Bots")
if st.session_state.bots:
    # On affiche un vrai tableau interactif Streamlit, c'est plus solide
    config_df = pd.DataFrame(list(st.session_state.bots.values()))
    st.dataframe(config_df[["id", "actif", "p_achat", "p_vente", "mise", "etape", "gain_cumule"]])

st.divider()
for m in reversed(st.session_state.logs[-5:]): st.write(m)
