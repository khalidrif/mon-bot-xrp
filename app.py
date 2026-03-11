import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION
st.set_page_config(page_title="XRP Sniper REAL TRADING", layout="wide")
symbol = "XRP/USDC"
conn = st.connection("gsheets", type=GSheetsConnection)
st_autorefresh(interval=30000, key="bot_refresh")

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# 2. CONNEXIONS KRAKEN
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
        df = conn.read(ttl=5)
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
    except: st.error("❌ Erreur Sauvegarde Cloud")

# 4. INITIALISATION
if "bots" not in st.session_state:
    cfg = load_config()
    if cfg: st.session_state.bots = cfg
    else:
        st.error("⚠️ Impossible de lire Google Sheets.")
        st.stop()

if "run" not in st.session_state: st.session_state.run = False

# 5. BOUCLE DE TRADING RÉEL
def run_cycle():
   # --- NOUVEAU BLOC SANS CACHE ---
    try:
        # On force Kraken à ne pas envoyer de vieux prix
        ticker = exchange.fetch_ticker(symbol, params={'cache': time.time()})
        price = ticker["last"]
        
        # On vérifie si le prix bouge
        if st.session_state.get("price") != price:
            log(f"⚡ NOUVEAU PRIX : {price:.4f}")
        else:
            log(f"🔄 Prix stable : {price:.4f}")

        st.session_state.price = price
        
        # Mise à jour des soldes en temps réel
        bal = exchange.fetch_balance()
        usdc_dispo = bal["free"].get("USDC", 0.0)
        st.session_state.usdc = usdc_dispo
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
        
    except Exception as e:
        log(f"⚠️ Erreur Flux : {str(e)[:30]}")
        price = st.session_state.get("price")
        usdc_dispo = st.session_state.get("usdc", 0.0)


    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot["actif"]: continue
        
        # --- ACHAT ---
        if bot["etape"] == "ATTENTE_ACHAT" and price and price <= bot["p_achat"]:
            if usdc_dispo >= bot["mise"]:
                try:
                    qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.985) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"] = qty
                    bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                    log(f"🟢 BOT {i} : ACHAT de {qty} XRP")
                except Exception as e: log(f"❌ BOT {i} ACHAT : {str(e)[:40]}")
            else: log(f"⚠️ BOT {i} : Solde insuffisant")

        # --- VENTE ---
        elif bot["etape"] == "ATTENTE_VENTE" and price and price >= bot["p_vente"]:
            if bot["qty"] > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.998))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - bot["mise"]
                    bot["gain_cumule"] += gain
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"🔴 BOT {i} : VENTE (Gain: {gain:.2f}$)")
                except Exception as e: log(f"❌ BOT {i} VENTE : {str(e)[:40]}")

run_cycle()

# 6. INTERFACE (UI)
st.title("🚀 XRP Sniper REAL TRADING")

with st.sidebar:
    st.header("⚙️ Configuration")
    id_bot = st.selectbox("Sélectionner Bot", range(1, 51))
    b = st.session_state.bots[id_bot]
    b["actif"] = st.toggle("Activer", b["actif"])
    b["p_achat"] = st.number_input("Prix Achat", value=b["p_achat"], format="%.4f")
    b["p_vente"] = st.number_input("Prix Vente", value=b["p_vente"], format="%.4f")
    b["mise"] = st.number_input("Mise ($)", value=b["mise"])
    if st.button("💾 Sauvegarder"):
        save_config(st.session_state.bots)
        st.success("Cerveau mis à jour !")
    st.divider()
    if st.button("🚀 DÉMARRER TOUT", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False

# Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price',0):.4f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc',0):.2f}")
m3.metric("Solde XRP", f"{st.session_state.get('xrp',0):.2f}")

# Tableau des 50 Bots (CORRIGÉ)
st.divider()
st.subheader("📊 État des 50 Bots")
titres = st.columns([0.5, 1, 1, 1, 1.5, 1])
titres[0].write("**ID**")
titres[1].write("**Status**")
titres[2].write("**Achat**")
titres[3].write("**Vente**")
titres[4].write("**Étape**")
titres[5].write("**Gain**")

for i in range(1, 51):
    bt = st.session_state.bots.get(i)
    if not bt: continue
    row = st.columns([0.5, 1, 1, 1, 1.5, 1])
    row[0].write(f"#{i}")
    row[1].write("✅" if bt["actif"] else "⚪")
    row[2].write(f"{bt['p_achat']:.4f}")
    row[3].write(f"{bt['p_vente']:.4f}")
    icon = "🔵" if "ACHAT" in bt["etape"] else "🟢"
    row[4].write(f"{icon} {bt['etape']}")
    row[5].write(f"{bt['gain_cumule']:.2f}$")

st.divider()
st.subheader("📜 Logs")
for m in reversed(st.session_state.logs[-15:]): st.write(m)
    st.caption("Version du bot : MISE À JOUR SANS CACHE - 05:05")



