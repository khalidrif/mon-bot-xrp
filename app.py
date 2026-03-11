import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="XRP Sniper Pro Cloud", layout="wide")
symbol = "XRP/USDC"

# 2. CONNEXIONS (Google Sheets & Kraken)
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
exchange = get_exchange()

# 3. AUTO-REFRESH (30 secondes)
st_autorefresh(interval=30000, key="bot_refresh")

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# 4. FONCTIONS DE SAUVEGARDE CLOUD
def load_config():
    try:
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
    except:
        return None

def save_config(bots_dict):
    try:
        data = [{"id": i, **b} for i, b in bots_dict.items()]
        df = pd.DataFrame(data)
        conn.update(data=df)
    except:
        st.error("❌ Erreur de sauvegarde sur Google Sheets")

# 5. INITIALISATION DES ÉTATS
if "bots" not in st.session_state:
    cfg = load_config()
    if cfg: st.session_state.bots = cfg
    else:
        st.error("⚠️ Données Google Sheets introuvables. Vérifiez votre tableau !")
        st.stop()

if "run" not in st.session_state:
    st.session_state.run = False

# 6. BOUCLE DE TRADING (EXECUTION)
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
        st.session_state.price = price
        
        bal = exchange.fetch_balance()
        st.session_state.usdc = bal["free"].get("USDC", 0.0)
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
        log(f"Prix XRP : {price:.4f}")
    except:
        price = st.session_state.get("price")

    if not st.session_state.run:
        return

    # Logique d'achat/vente pour les bots actifs
    for i, bot in st.session_state.bots.items():
        if not bot["actif"]: continue
        
        if bot["etape"] == "ATTENTE_ACHAT" and price and price <= bot["p_achat"]:
            # Ici tu peux ajouter l'ordre exchange.create_market_buy_order
            log(f"🟢 Bot {i} : Signal ACHAT déclenché à {price}")
        elif bot["etape"] == "ATTENTE_VENTE" and price and price >= bot["p_vente"]:
            # Ici tu peux ajouter l'ordre exchange.create_market_sell_order
            log(f"🔴 Bot {i} : Signal VENTE déclenché à {price}")

run_cycle()

# 7. INTERFACE UTILISATEUR (UI)
st.title("🚀 XRP Sniper Pro Cloud")

# Sidebar pour réglages
with st.sidebar:
    st.header("⚙️ Configuration")
    id_bot = st.selectbox("Sélectionner un Bot", range(1, 51))
    b_sel = st.session_state.bots[id_bot]
    
    b_sel["actif"] = st.toggle("Activer le Bot", b_sel["actif"])
    b_sel["p_achat"] = st.number_input("Prix Achat", value=b_sel["p_achat"], format="%.4f")
    b_sel["p_vente"] = st.number_input("Prix Vente", value=b_sel["p_vente"], format="%.4f")
    b_sel["mise"] = st.number_input("Mise ($)", value=b_sel["mise"])
    
    if st.button("💾 Sauvegarder sur Cloud"):
        st.session_state.bots[id_bot] = b_sel
        save_config(st.session_state.bots)
        st.success("Config enregistrée !")

    st.divider()
    if st.button("🚀 DÉMARRER TOUT", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False

# Métriques du haut
p_display = st.session_state.get("price", 0)
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{p_display:.4f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc', 0):.2f} $")
m3.metric("Solde XRP", f"{st.session_state.get('xrp', 0):.2f}")

# Tableau des 50 bots
st.divider()
st.subheader("📊 État des 50 Bots")
cols = st.columns([0.5, 1, 1, 1, 1.5, 1])
cols[0].write("**ID**"); cols[1].write("**Statut**"); cols[2].write("**Achat**")
cols[3].write("**Vente**"); cols[4].write("**Étape**"); cols[5].write("**Gain**")

for i in range(1, 51):
    b = st.session_state.bots.get(i)
    if not b: continue
    c = st.columns([0.5, 1, 1, 1, 1.5, 1])
    c[0].write(f"#{i}")
    c[1].write("✅ ON" if b["actif"] else "⚪ OFF")
    c[2].write(f"{b['p_achat']:.4f}")
    c[3].write(f"{b['p_vente']:.4f}")
    c[4].write(f"{'🔵' if 'ACHAT' in b['etape'] else '🟢'} {b['etape']}")
    c[5].write(f"{b['gain_cumule']:.2f} $")

# Logs
st.divider()
st.subheader("📜 Logs")
for m in reversed(st.session_state.logs[-15:]):
    st.write(m)
