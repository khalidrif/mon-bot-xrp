import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION
st.set_page_config(page_title="XRP SNIPER PRO - CONTROL CENTER", layout="wide")
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
    except: st.error("❌ Erreur Sauvegarde Cloud")

# 4. INITIALISATION
if "bots" not in st.session_state:
    cfg = load_config()
    if cfg: st.session_state.bots = cfg
    else: st.stop()

if "run" not in st.session_state: st.session_state.run = False

# 5. BOUCLE DE TRADING
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = (ticker["bid"] + ticker["ask"]) / 2
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
        mise_actu = bot["mise"] + bot["gain_cumule"]

        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            if usdc_dispo >= mise_actu:
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"] = qty; bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots); log(f"🟢 Bot {i} : ACHAT {qty} XRP")
                except: log(f"❌ Erreur Achat Bot {i}")
        
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            if bot["qty"] > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - mise_actu
                    bot["gain_cumule"] += gain; bot["qty"] = 0; bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots); log(f"🔴 Bot {i} : VENTE Gain {gain:.2f}$")
                except: log(f"❌ Erreur Vente Bot {i}")

run_cycle()

# 6. INTERFACE (UI)
st.title("🚀 XRP SNIPER - CONTROL CENTER")

with st.sidebar:
    st.header("⚙️ Config Rapide")
    id_bot = st.selectbox("Bot", range(1, 51))
    b = st.session_state.bots[id_bot]
    b["p_achat"] = st.number_input("Achat", value=b["p_achat"], format="%.4f")
    b["p_vente"] = st.number_input("Vente", value=b["p_vente"], format="%.4f")
    b["mise"] = st.number_input("Mise", value=b["mise"])
    if st.button("💾 Sauver Config"):
        save_config(st.session_state.bots); st.success("OK")
    st.divider()
    if st.button("🚀 START TOUT", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False

# METRICS
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price',0):.5f}")
m2.metric("USDC", f"{st.session_state.get('usdc',0):.2f}$")
m3.metric("XRP", f"{st.session_state.get('xrp',0):.2f}")

# TABLEAU DE CONTRÔLE INDIVIDUEL
st.divider()
st.subheader("📊 Gestion des 50 Bots")
cols = st.columns([0.4, 0.4, 0.7, 0.7, 0.7, 1.2, 0.6, 0.6, 1])
cols[0].write("**ID**"); cols[1].write("**Stat**"); cols[2].write("**Achat**")
cols[3].write("**Vente**"); cols[4].write("**Mise**"); cols[5].write("**Étape**")
cols[6].write("**Go**"); cols[7].write("**Clr**"); cols[8].write("**Gain**")

for i in range(1, 51):
    bt = st.session_state.bots.get(i)
    r = st.columns([0.4, 0.4, 0.7, 0.7, 0.7, 1.2, 0.6, 0.6, 1])
    r[0].write(f"#{i}")
    r[1].write("✅" if bt["actif"] else "⚪")
    r[2].write(f"{bt['p_achat']:.3f}")
    r[3].write(f"{bt['p_vente']:.3f}")
    r[4].write(f"{bt['mise'] + bt['gain_cumule']:.1f}$")
    icon = "🔵" if "ACHAT" in bt["etape"] else "🟢"
    r[5].write(f"{icon} {bt['etape']}")
    
    # Bouton Start/Stop individuel
    if bt["actif"]:
        if r[6].button("🛑", key=f"s_{i}"):
            st.session_state.bots[i]["actif"] = False
            save_config(st.session_state.bots); st.rerun()
    else:
        if r[6].button("🚀", key=f"g_{i}"):
            st.session_state.bots[i]["actif"] = True
            save_config(st.session_state.bots); st.rerun()
            
    # Bouton Réinitialiser (🗑️)
    if r[7].button("🗑️", key=f"r_{i}"):
        st.session_state.bots[i] = {"id":i,"actif":False,"p_achat":1.35,"p_vente":1.38,"mise":15.0,"etape":"ATTENTE_ACHAT","qty":0.0,"gain_cumule":0.0}
        save_config(st.session_state.bots); st.rerun()

    gain = bt["gain_cumule"]
    color = "green" if gain > 0 else "white"
    r[8].markdown(f":{color}[{gain:.2f}$]")

st.divider()
for m in reversed(st.session_state.logs[-10:]): st.write(m)
