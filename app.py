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

# 2. CONNEXIONS
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
exchange = get_exchange()

# 3. FONCTIONS CLOUD
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
    else: st.stop()

if "run" not in st.session_state: st.session_state.run = False

# 5. BOUCLE DE TRADING RÉEL 
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
        st.session_state.price = price
        
        bal = exchange.fetch_balance()
        usdc_dispo = bal["free"].get("USDC", 0.0)
        st.session_state.usdc = usdc_dispo
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
        log(f"Prix XRP : {price:.4f}")
    except:
        price = st.session_state.get("price")
        usdc_dispo = st.session_state.get("usdc", 0.0)

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot["actif"]: continue
        
        # --- ACTION ACHAT ---
        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            if usdc_dispo >= bot["mise"]:
                try:
                    # Calcul quantité avec 1.5% de marge pour les frais
                    qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.985) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    
                    bot["qty"] = qty
                    bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                    log(f"🟢 BOT {i} : ACHAT RÉEL de {qty} XRP")
                except Exception as e:
                    log(f"❌ BOT {i} ERREUR ACHAT : {str(e)[:50]}")
            else:
                log(f"⚠️ BOT {i} : Solde USDC insuffisant")

        # --- ACTION VENTE ---
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            if bot["qty"] > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.998))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    
                    gain = (price * qty_sell) - bot["mise"]
                    bot["gain_cumule"] += gain
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"🔴 BOT {i} : VENTE RÉELLE (Gain: {gain:.2f}$)")
                except Exception as e:
                    log(f"❌ BOT {i} ERREUR VENTE : {str(e)[:50]}")

run_cycle()

# 6. INTERFACE
st.title("🚀 XRP Sniper REAL TRADING")

with st.sidebar:
    st.header("⚙️ Config")
    id_bot = st.selectbox("Bot", range(1, 51))
    b = st.session_state.bots[id_bot]
    b["actif"] = st.toggle("Activer", b["actif"])
    b["p_achat"] = st.number_input("Prix Achat", value=b["p_achat"], format="%.4f")
    b["p_vente"] = st.number_input("Prix Vente", value=b["p_vente"], format="%.4f")
    b["mise"] = st.number_input("Mise ($)", value=b["mise"])
    if st.button("💾 Sauvegarder"):
        save_config(st.session_state.bots)
        st.success("Cloud mis à jour")
    st.divider()
    if st.button("🚀 DÉMARRER TOUT", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False

# Metrics & Tableau
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price',0):.4f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc',0):.2f}")
m3.metric("Solde XRP", f"{st.session_state.get('xrp',0):.2f}")

st.divider()
st.subheader("📊 État des 50 Bots")
# Affichage simplifié en colonnes
cols = st.columns([0.5, 1, 1, 1, 1.5, 1])
cols.write("**ID**"); cols.write("**Status**"); cols.write("**Achat**"); cols.write("**Vente**"); cols.write("**Étape**"); cols.write("**Gain**")

for i in range(1, 51):
    bt = st.session_state.bots.get(i)
    c = st.columns([0.5, 1, 1, 1, 1.5, 1])
    c.write(f"#{i}")
    c.write("✅" if bt["actif"] else "⚪")
    c.write(f"{bt['p_achat']:.4f}")
    c.write(f"{bt['p_vente']:.4f}")
    c.write(f"{'🔵' if 'ACHAT' in bt['etape'] else '🟢'} {bt['etape']}")
    c.write(f"{bt['gain_cumule']:.2f}$")

st.divider()
for m in reversed(st.session_state.logs[-15:]): st.write(m)
