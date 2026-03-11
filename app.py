import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="XRP Sniper Cloud", layout="wide")
symbol = "XRP/USDC"

# 2. CONNEXION GOOGLE SHEETS (Ton nouveau disque dur)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. RAFRAÎCHISSEMENT AUTO (Toutes les 30 secondes)
st_autorefresh(interval=30000, key="bot_refresh")

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# 4. CHARGEMENT / SAUVEGARDE VIA LE CLOUD
def load_config():
    try:
        # Lit la feuille Google Sheets (cache de 5s pour être réactif)
        df = conn.read(ttl=5)
        bots = {}
        for _, row in df.iterrows():
            bots[int(row['id'])] = {
                "id": int(row['id']),
                "actif": bool(row['actif']),
                "p_achat": float(row['p_achat']),
                "p_vente": float(row['p_vente']),
                "mise": float(row['mise']),
                "etape": str(row['etape']),
                "qty": float(row['qty']),
                "gain_cumule": float(row['gain_cumule'])
            }
        return bots
    except Exception as e:
        st.error(f"Erreur Google Sheets : {e}")
        return None

def save_config(bots_dict):
    try:
        data = [{"id": i, **b} for i, b in bots_dict.items()]
        df = pd.DataFrame(data)
        conn.update(data=df)
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")

# 5. INITIALISATION
if "bots" not in st.session_state:
    cfg = load_config()
    if cfg:
        st.session_state.bots = cfg
    else:
        st.warning("⚠️ En attente de données sur Google Sheets...")
        st.stop()

if "run" not in st.session_state:
    st.session_state.run = False

# 6. CONNEXION KRAKEN
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })

exchange = get_exchange()

# 7. BOUCLE DE TRADING (C'est ici que le prix se met à jour)
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
        st.session_state.price = price
        log(f"Prix XRP : {price}")
    except Exception as e:
        price = st.session_state.get("price")
        log(f"⚠️ Erreur API Kraken")

    if not st.session_state.run:
        return

    # Logique simplifiée pour test sur le Bot 1
    for i, bot in st.session_state.bots.items():
        if bot["actif"]:
            # Ici tu peux remettre ta logique d'achat/vente complète
            log(f"Bot {i} surveille... (Prix: {price} / Seuil: {bot['p_achat']})")

run_cycle()

# 8. INTERFACE UTILISATEUR
st.title("🚀 XRP Sniper Pro (Cloud Edition)")

col1, col2 = st.columns(2)
with col1:
    st.metric("Prix Actuel", f"{st.session_state.get('price', '...')}")
with col2:
    if st.button("🚀 DÉMARRER LE BOT", use_container_width=True):
        st.session_state.run = True
    if st.button("🛑 STOP", use_container_width=True):
        st.session_state.run = False

st.divider()
st.subheader("Logs en temps réel")
for message in reversed(st.session_state.logs[-10:]):
    st.write(message)
