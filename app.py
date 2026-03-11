import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="XRP SNIPER CLOUD PRO", layout="wide")
symbol = "XRP/USDC"
conn = st.connection("gsheets", type=GSheetsConnection)
st_autorefresh(interval=30000, key="bot_refresh")

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# 2. CONNEXION KRAKEN (SANS CACHE)
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
exchange = get_exchange()

# 3. FONCTIONS CLOUD (GOOGLE SHEETS)
def load_config():
    try:
        df = conn.read(ttl=1)
        bots = {}
        for _, row in df.iterrows():
            idx = int(row['id'])
            bots[idx] = {
                "id": idx, 
                "actif": bool(row['actif']),
                "p_achat": float(row['p_achat']), 
                "p_vente": float(row['p_vente']),
                "mise": float(row['mise']), 
                "etape": str(row['etape']),
                "qty": float(row.get('qty', 0)), 
                "gain_cumule": float(row.get('gain_cumule', 0)),
                "cycles": int(row.get('cycles', 0))
            }
        return bots
    except Exception as e:
        st.error(f"Erreur Lecture Sheets: {e}")
        return None

def save_config(bots_dict):
    try:
        data = [v for k, v in bots_dict.items()]
        df = pd.DataFrame(data)
        conn.update(data=df)
    except Exception as e:
        st.error(f"Erreur Sauvegarde Cloud: {e}")

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
        if not bot.get("actif", False): continue
        mise_actu = bot.get("mise", 15.0) + bot.get("gain_cumule", 0.0)

        # --- ACHAT ---
        if bot.get("etape") == "ATTENTE_ACHAT" and price <= bot.get("p_achat"):
            if usdc_dispo >= mise_actu:
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"] = qty
                    bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                    log(f"🟢 Bot {i} : ACHAT Snowball {mise_actu:.2f}$")
                except: log(f"❌ Erreur Achat Bot {i}")

        # --- VENTE ---
        elif bot.get("etape") == "ATTENTE_VENTE" and price >= bot.get("p_vente"):
            if bot.get("qty", 0) > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - mise_actu
                    bot["gain_cumule"] += gain
                    bot["cycles"] = bot.get("cycles", 0) + 1
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"💰 Bot {i} : VENTE +{gain:.2f}$ (Total: {bot['gain_cumule']:.2f}$)")
                except: log(f"❌ Erreur Vente Bot {i}")

run_cycle()

# 6. INTERFACE (UI)
st.title("🚀 XRP SNIPER - CONTROL CENTER")
st.caption("Mode Boule de Neige Actif | Google Sheets | Flux 30s")

with st.sidebar:
    st.header("⚙️ Configuration")
    id_bot = st.selectbox("Sélectionner Bot", range(1, 51))
    b_sel = st.session_state.bots.get(id_bot, {})
    if b_sel:
        b_sel["p_achat"] = st.number_input("Prix Achat", value=b_sel.get("p_achat", 1.35), format="%.4f")
        b_sel["p_vente"] = st.number_input("Prix Vente", value=b_sel.get("p_vente", 1.38), format="%.4f")
        b_sel["mise"] = st.number_input("Mise de base ($)", value=b_sel.get("mise", 15.0))
        if st.button("💾 Sauver Configuration"):
            save_config(st.session_state.bots)
            st.success("Config synchronisée !")
    st.divider()
    if st.button("🚀 DÉMARRER TOUT", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False

# METRICS
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP (Moyenne)", f"{st.session_state.get('price',0):.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc',0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp',0):.2f}")

# TABLEAU DE GESTION
st.divider()
st.subheader("📊 État des 50 Bots")
h = st.columns([0.4, 0.4, 0.8, 0.8, 0.8, 1.2, 0.5, 0.6, 0.6, 1])
h[0].write("**ID**"); h[1].write("**St**"); h[2].write("**Achat**"); h[3].write("**Vente**")
h[4].write("**Mise**"); h[5].write("**Étape**"); h[6].write("**Cy**"); h[7].write("**Go**")
h[8].write("**Clr**"); h[9].write("**Gain**")

for i in range(1, 51):
    bt = st.session_state.bots.get(i)
    if bt is None: continue
    
    r = st.columns([0.4, 0.4, 0.8, 0.8, 0.8, 1.2, 0.5, 0.6, 0.6, 1])
    r[0].write(f"#{i}")
    is_actif = bt.get("actif", False)
    r[1].write("✅" if is_actif else "⚪")
    r[2].write(f"{bt.get('p_achat', 0):.3f}")
    r[3].write(f"{bt.get('p_vente', 0):.3f}")
    
    mise_actu = bt.get('mise', 15.0) + bt.get('gain_cumule', 0.0)
    r[4].write(f"{mise_actu:.1f}$")
    
    etape = bt.get('etape', 'ATTENTE_ACHAT')
    icon = "🔵" if "ACHAT" in etape else "🟢"
    r[5].write(f"{icon} {etape[:6]}")
    
    r[6].write(str(bt.get('cycles', 0)))
    
    if is_actif:
        if r[7].button("🛑", key=f"s_{i}"):
            st.session_state.bots[i]["actif"] = False
            save_config(st.session_state.bots); st.rerun()
    else:
        if r[7].button("🚀", key=f"g_{i}"):
            st.session_state.bots[i]["actif"] = True
            save_config(st.session_state.bots); st.rerun()
            
    if r[8].button("🗑️", key=f"r_{i}"):
        st.session_state.bots[i] = {"id":i,"actif":False,"p_achat":1.35,"p_vente":1.38,"mise":15.0,"etape":"ATTENTE_ACHAT","qty":0.0,"gain_cumule":0.0,"cycles":0}
        save_config(st.session_state.bots); st.rerun()

    gain = bt.get('gain_cumule', 0.0)
    color = "green" if gain > 0 else "white"
    r[9].markdown(f":{color}[{gain:.2f}$]")

st.divider()
for m in reversed(st.session_state.logs[-10:]): st.write(m)
