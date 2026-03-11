import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION
st.set_page_config(page_title="XRP SNIPER SNOWBALL PRO", layout="wide")
symbol = "XRP/USDC"
conn = st.connection("gsheets", type=GSheetsConnection)
st_autorefresh(interval=30000, key="bot_refresh")

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# 2. CONNEXION KRAKEN
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
exchange = get_exchange()

# 3. FONCTIONS CLOUD (Google Sheets)
def load_config():
    try:
        df = conn.read(ttl=1)
        bots = {}
        for _, row in df.iterrows():
            bots[int(row['id'])] = {
                "id": int(row['id']), "actif": bool(row['actif']),
                "p_achat": float(row['p_achat']), "p_vente": float(row['p_vente']),
                "mise": float(row['mise']), "etape": str(row['etape']),
                "qty": float(row['qty']), "gain_cumule": float(row['gain_cumule'])
            }
        return bots
    except: return None

def save_config(bots_dict):
    try:
        data = [{"id": i, **b} for i, b in bots_dict.items()]
        df = pd.DataFrame(data)
        conn.update(data=df)
    except: st.error("❌ Erreur Sauvegarde Google Sheets")

# 4. INITIALISATION
if "bots" not in st.session_state:
    cfg = load_config()
    if cfg: st.session_state.bots = cfg
    else: st.stop()

if "run" not in st.session_state: st.session_state.run = False

# 5. BOUCLE DE TRADING (BOULE DE NEIGE)
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = (ticker["bid"] + ticker["ask"]) / 2 # Prix mobile
        st.session_state.price = price
        
        bal = exchange.fetch_balance()
        usdc_dispo = bal["free"].get("USDC", 0.0)
        st.session_state.usdc = usdc_dispo
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
        log(f"⚡ Prix Marché : {price:.5f}")
    except:
        price = st.session_state.get("price", 0)
        usdc_dispo = st.session_state.get("usdc", 0)

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot["actif"]: continue
        
        # MISE ACTUELLE (Initiale + Gains)
        mise_actuelle = bot["mise"] + bot["gain_cumule"]

        # --- ACHAT ---
        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            if usdc_dispo >= mise_actuelle:
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actuelle * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"] = qty
                    bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                    log(f"🟢 BOT {i} : ACHAT Snowball {mise_actuelle:.2f}$")
                except: log(f"❌ Erreur Achat Bot {i}")

        # --- VENTE ---
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            if bot["qty"] > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain_net = (price * qty_sell) - mise_actuelle
                    bot["gain_cumule"] += gain_net
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"💰 BOT {i} : VENTE ! Gain Net: +{gain_net:.2f}$")
                except: log(f"❌ Erreur Vente Bot {i}")

run_cycle()

# 6. INTERFACE (UI)
st.title("🚀 XRP SNIPER PRO - SNOWBALL EDITION")

with st.sidebar:
    st.header("⚙️ Config")
    id_bot = st.selectbox("Sélectionner Bot", range(1, 51))
    b = st.session_state.bots[id_bot]
    b["actif"] = st.toggle("Activer le Bot", b["actif"])
    b["p_achat"] = st.number_input("Prix Achat", value=b["p_achat"], format="%.4f")
    b["p_vente"] = st.number_input("Prix Vente", value=b["p_vente"], format="%.4f")
    b["mise"] = st.number_input("Mise de départ ($)", value=b["mise"])
    if st.button("💾 Sauvegarder sur Cloud"):
        save_config(st.session_state.bots)
        st.success("Config enregistrée !")
    st.divider()
    if st.button("🚀 DÉMARRER TOUT", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False

# METRICS
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price', 0):.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc', 0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp', 0):.2f}")

# TABLEAU DES BOTS AVEC EFFET BOULE DE NEIGE
st.divider()
st.subheader("📊 Suivi des 50 Bots (Boule de Neige)")
titres = st.columns([0.5, 0.8, 1, 1, 1, 1, 1, 1])
titres[0].write("**ID**")
titres[1].write("**Status**")
titres[2].write("**Achat**")
titres[3].write("**Vente**")
titres[4].write("**Mise Init.**")
titres[5].write("**Mise Actu.**") # Boule de neige
titres[6].write("**Étape**")
titres[7].write("**Profit Net**")

for i in range(1, 51):
    bt = st.session_state.bots.get(i)
    if not bt: continue
    row = st.columns([0.5, 0.8, 1, 1, 1, 1, 1, 1])
    row[0].write(f"#{i}")
    row[1].write("✅" if bt["actif"] else "⚪")
    row[2].write(f"{bt['p_achat']:.4f}")
    row[3].write(f"{bt['p_vente']:.4f}")
    row[4].write(f"{bt['mise']:.1f}$")
    
    # Mise actuelle (Boule de neige)
    mise_actu = bt["mise"] + bt["gain_cumule"]
    row[5].write(f"**{mise_actu:.2f}$**")
    
    icon = "🔵" if "ACHAT" in bt["etape"] else "🟢"
    row[6].write(f"{icon} {bt['etape']}")
    
    gain = bt["gain_cumule"]
    color = "green" if gain > 0 else "white"
    row[7].markdown(f":{color}[{gain:.2f}$]")

st.divider()
for m in reversed(st.session_state.logs[-15:]): st.write(m)
