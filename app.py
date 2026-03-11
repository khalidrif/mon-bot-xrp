import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION PAGE
st.set_page_config(page_title="XRP SNIPER CLOUD PRO", layout="wide")
symbol = "XRP/USDC"
conn = st.connection("gsheets", type=GSheetsConnection)

# RAFRAÎCHISSEMENT AUTO (40s pour stabilité Cloud)
st_autorefresh(interval=40000, key="bot_refresh")

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

# 3. FONCTIONS CLOUD (SÉCURISÉES SANS CACHE)
def load_config():
    try:
        df = conn.read(ttl=0) 
        bots = {}
        for _, row in df.iterrows():
            idx = int(row['id'])
            bots[idx] = {
                "id": idx, 
                "actif": bool(row.get('actif', False)),
                "p_achat": float(row.get('p_achat', 1.35)), 
                "p_vente": float(row.get('p_vente', 1.38)),
                "mise": float(row.get('mise', 15.0)), 
                "etape": str(row.get('etape', 'ATTENTE_ACHAT')),
                "qty": float(row.get('qty', 0)), 
                "gain_cumule": float(row.get('gain_cumule', 0)),
                "cycles": int(row.get('cycles', 0))
            }
        return bots
    except:
        return st.session_state.get("bots", {})

def save_config(bots_dict):
    try:
        data = [v for k, v in bots_dict.items()]
        df = pd.DataFrame(data)
        conn.update(data=df)
        st.toast("✅ Synchronisation Sheets OK")
    except:
        st.error("❌ Erreur de sauvegarde Cloud")

# 4. INITIALISATION
if "bots" not in st.session_state:
    cfg = load_config()
    if cfg: 
        st.session_state.bots = cfg
    else:
        st.session_state.bots = {i: {"id":i,"actif":False,"p_achat":1.35,"p_vente":1.38,"mise":15.0,"etape":"ATTENTE_ACHAT","qty":0.0,"gain_cumule":0.0,"cycles":0} for i in range(1,51)}

if "run" not in st.session_state: 
    st.session_state.run = False

# 5. BOUCLE DE TRADING (RÉALITÉ DU MARCHÉ)
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol, params={'nonce': str(int(time.time()*1000))})
        price = (ticker["bid"] + ticker["ask"]) / 2
        st.session_state.price = price
        bal = exchange.fetch_balance()
        usdc_dispo = bal["free"].get("USDC", 0.0)
        st.session_state.usdc = usdc_dispo
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
        log(f"🎯 Flux Direct : {price:.5f}")
    except:
        price = st.session_state.get("price", 0)
        usdc_dispo = st.session_state.get("usdc", 0)

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot.get("actif", False): continue
        mise_actu = bot.get("mise", 15.0) + bot.get("gain_cumule", 0.0)

        # --- ACHAT ---
        if bot.get("etape") == "ATTENTE_ACHAT" and price <= bot.get("p_achat"):
            if usdc_dispo >= mise_actu:
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"] = qty; bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots); log(f"🟢 Bot {i} : ACHAT {qty} XRP")
                except: log(f"❌ Erreur Achat Bot {i}")
        
        # --- VENTE ---
        elif bot.get("etape") == "ATTENTE_VENTE" and price >= bot.get("p_vente"):
            if bot.get("qty", 0) > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - mise_actu
                    bot["gain_cumule"] += gain; bot["cycles"] = bot.get("cycles", 0) + 1
                    bot["qty"] = 0; bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots); log(f"💰 Bot {i} : VENTE Gain {gain:.2f}$")
                except: log(f"❌ Erreur Vente Bot {i}")

run_cycle()

# 6. INTERFACE (UI)
st.title("🚀 SNIPER PRO CONTROL")

with st.sidebar:
    st.header("⚙️ Configuration")
    id_bot = st.selectbox("Choisir Bot", range(1, 51))
    b = st.session_state.bots.get(id_bot, {})
    
    new_achat = st.number_input("Achat", value=float(b.get("p_achat", 1.35)), format="%.4f", key=f"a_{id_bot}")
    new_vente = st.number_input("Vente", value=float(b.get("p_vente", 1.38)), format="%.4f", key=f"v_{id_bot}")
    new_mise = st.number_input("Mise ($)", value=float(b.get("mise", 15.0)), key=f"m_{id_bot}")
    
    if st.button("💾 SAUVEGARDER"):
        st.session_state.bots[id_bot]["p_achat"] = new_achat
        st.session_state.bots[id_bot]["p_vente"] = new_vente
        st.session_state.bots[id_bot]["mise"] = new_mise
        save_config(st.session_state.bots); st.rerun()

    st.divider()
    if st.button("🚀 START TOUT"): st.session_state.run = True; st.rerun()
    if st.button("🛑 STOP TOUT"): st.session_state.run = False; st.rerun()

# METRICS
p_val = st.session_state.get("price", 0)
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{p_val:.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc', 0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp', 0):.2f}")

# TABLEAU DE GESTION
st.divider()
st.subheader("📊 Gestion des 50 Bots")
h = st.columns([0.4, 0.4, 0.7, 0.7, 0.7, 0.6, 1.2, 0.4, 0.5, 0.5, 1])
h.write("**ID**"); h.write("**St**"); h.write("**Achat**"); h.write("**Vente**")
h.write("**Mise**"); h.write("**Qty**"); h.write("**Étape**")
h.write("**Cy**"); h.write("**Go**"); h.write("**Clr**"); h.write("**Gain**")

for i in range(1, 51):
    bt = st.session_state.bots.get(i)
    if not bt: continue
    r = st.columns([0.4, 0.4, 0.7, 0.7, 0.7, 0.6, 1.2, 0.4, 0.5, 0.5, 1])
    r.write(f"#{i}")
    is_actif = bt.get("actif", False)
    r.write("✅" if is_actif else "⚪")
    r.write(f"{bt.get('p_achat'):.3f}"); r.write(f"{bt.get('p_vente'):.3f}")
    
    mise_actu = bt.get('mise', 15.0) + bt.get('gain_cumule', 0.0)
    r.write(f"{mise_actu:.1f}$")
    r.write(f"{bt.get('qty', 0.0):.1f}")
    
    etape = bt.get('etape', 'ATTENTE_ACHAT')
    icon = "🔵" if "ACHAT" in etape else "🟢"
    r.write(f"{icon} {etape[:6]}")
    r.write(str(bt.get("cycles", 0)))
    
    if is_actif:
        if r.button("🛑", key=f"s_{i}"):
            st.session_state.bots[i]["actif"] = False
            save_config(st.session_state.bots); st.rerun()
    else:
        if r.button("🚀", key=f"g_{i}"):
            st.session_state.bots[i]["actif"] = True
            save_config(st.session_state.bots); st.rerun()
            
    if r.button("🗑️", key=f"r_{i}"):
        st.session_state.bots[i] = {"id":i,"actif":False,"p_achat":1.35,"p_vente":1.38,"mise":15.0,"etape":"ATTENTE_ACHAT","qty":0.0,"gain_cumule":0.0,"cycles":0}
        save_config(st.session_state.bots); st.rerun()

    g = bt.get("gain_cumule", 0.0)
    r.markdown(f":{'green' if g > 0 else 'white'}[{g:.2f}$]")

st.divider()
for m in reversed(st.session_state.logs[-10:]): st.write(m)
