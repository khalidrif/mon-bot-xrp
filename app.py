import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION PAGE
st.set_page_config(page_title="XRP SNIPER TOTAL CONTROL", layout="wide")
symbol = "XRP/USDC"
conn = st.connection("gsheets", type=GSheetsConnection)
st_autorefresh(interval=40000, key="bot_refresh")

# Initialisation des verrous et logs
if "pending_orders" not in st.session_state:
    st.session_state.pending_orders = set()
if "logs" not in st.session_state:
    st.session_state.logs = []
if "run" not in st.session_state: 
    st.session_state.run = False

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
        if df.empty: return {}
        bots = {}
        for _, row in df.iterrows():
            idx = int(row['id'])
            bots[idx] = {
                "id": idx, "actif": bool(row.get('actif', False)),
                "p_achat": float(row.get('p_achat', 1.35)), "p_vente": float(row.get('p_vente', 1.38)),
                "mise": float(row.get('mise', 15.0)), "etape": str(row.get('etape', 'ATTENTE_ACHAT')),
                "qty": float(row.get('qty', 0)), "gain_cumule": float(row.get('gain_cumule', 0)),
                "cycles": int(row.get('cycles', 0))
            }
        return bots
    except:
        return {}

def save_config(bots_dict):
    try:
        data = [v for k, v in sorted(bots_dict.items())]
        df = pd.DataFrame(data)
        conn.update(data=df)
        st.toast("✅ Cloud Synchronisé")
    except:
        st.error("❌ Erreur de sauvegarde Cloud")

# 4. INITIALISATION (ANTI-PERTE & FORCE 50 BOTS)
if "bots" not in st.session_state or not st.session_state.bots:
    cfg = load_config()
    all_bots = {}
    for i in range(1, 51):
        if cfg and i in cfg:
            all_bots[i] = cfg[i]
        else:
            all_bots[i] = {
                "id": i, "actif": False, "p_achat": 1.35, "p_vente": 1.38,
                "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, 
                "gain_cumule": 0.0, "cycles": 0
            }
    st.session_state.bots = all_bots

# 5. BOUCLE DE TRADING (RÉEL + ANTI-DOUBLE)
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol, params={'nonce': str(int(time.time()*1000))})
        price = (ticker["bid"] + ticker["ask"]) / 2
        st.session_state.price = price
        bal = exchange.fetch_balance()
        usdc_dispo = bal["free"].get("USDC", 0.0)
        st.session_state.usdc = usdc_dispo
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
        log(f"⚡ Prix Marché : {price:.5f}")
    except:
        price = st.session_state.get("price", 0)

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot.get("actif", False) or i in st.session_state.pending_orders: 
            continue
        
        mise_actu = bot.get("mise", 15.0) + bot.get("gain_cumule", 0.0)

        # --- ACHAT ---
        if bot.get("etape") == "ATTENTE_ACHAT" and price <= bot.get("p_achat"):
            if usdc_dispo >= mise_actu:
                st.session_state.pending_orders.add(i)
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"] = qty; bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots); log(f"🟢 Bot {i} : ACHAT OK")
                except: pass
                finally: st.session_state.pending_orders.discard(i)

        # --- VENTE ---
        elif bot.get("etape") == "ATTENTE_VENTE" and price >= bot.get("p_vente"):
            if bot.get("qty", 0) > 0:
                st.session_state.pending_orders.add(i)
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - mise_actu
                    bot["gain_cumule"] += gain; bot["cycles"] = bot.get("cycles", 0) + 1
                    bot["qty"] = 0; bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots); log(f"💰 Bot {i} : VENTE OK (+{gain:.2f}$)")
                except: pass
                finally: st.session_state.pending_orders.discard(i)

run_cycle()

# 6. INTERFACE (UI)
st.title("🚀 XRP SNIPER TOTAL CONTROL")

with st.sidebar:
    st.header("⚙️ Configuration")
    id_bot = st.selectbox("Bot #", range(1, 51))
    b = st.session_state.bots.get(id_bot)
    
    new_achat = st.number_input("Achat", value=float(b.get("p_achat", 1.35)), format="%.4f", key=f"a_{id_bot}")
    new_vente = st.number_input("Vente", value=float(b.get("p_vente", 1.38)), format="%.4f", key=f"v_{id_bot}")
    new_mise = st.number_input("Mise ($)", value=float(b.get("mise", 15.0)), key=f"m_{id_bot}")
    
    if st.button("💾 SAUVEGARDER"):
        st.session_state.bots[id_bot].update({"p_achat": new_achat, "p_vente": new_vente, "mise": new_mise})
        save_config(st.session_state.bots); st.rerun()

    if st.button("🚀 START TOUT"): st.session_state.run = True; st.rerun()
    if st.button("🛑 STOP TOUT"): st.session_state.run = False; st.rerun()
    
    st.divider()
    if st.button("🔥 FORCER 50 BOTS DANS LE CLOUD"):
        save_config(st.session_state.bots)
        st.success("✅ Les 50 slots ont été créés !")

# Metrics
p_val = st.session_state.get("price", 0)
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{p_val:.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc', 0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp', 0):.2f}")

# TABLEAU DE GESTION
st.divider()
st.subheader("📊 État des Bots")
h = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.5, 0.5])
h[0].write("**ID**"); h[1].write("**St**"); h[2].write("**Achat**"); h[3].write("**Vente**")
h[4].write("**Mise**"); h[5].write("**Gain**"); h[6].write("**Qty**"); h[7].write("**Étape**")
h[8].write("**Cy**"); h[9].write("**Go**"); h[10].write("**Supp**")

for i in sorted(st.session_state.bots.keys()):
    bt = st.session_state.bots[i]
    r = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.5, 0.5])
    r[0].write(f"#{i}")
    r[1].write("✅" if bt.get("actif") else "⚪")
    r[2].write(f"{bt.get('p_achat'):.3f}"); r[3].write(f"{bt.get('p_vente'):.3f}")
    r[4].write(f"{bt.get('mise') + bt.get('gain_cumule'):.1f}$")
    g = bt.get("gain_cumule", 0.0)
    if g > 0: r[5].markdown(f"🟢 **+{g:.2f}$**")
    else: r[5].write(f"{g:.2f}$")
    r[6].write(f"{bt.get('qty', 0.0):.1f}")
    icon = "🔵" if "ACHAT" in bt.get("etape") else "🟢"
    r[7].write(f"{icon} {bt.get('etape')[:6]}")
    r[8].write(str(bt.get("cycles", 0)))
    if r[9].button("🚀" if not bt.get("actif") else "🛑", key=f"btn_{i}"):
        st.session_state.bots[i]["actif"] = not bt.get("actif")
        save_config(st.session_state.bots); st.rerun()
    if r[10].button("🗑️", key=f"del_{i}"):
        st.session_state.bots[i].update({"actif":False,"p_achat":1.35,"p_vente":1.38,"mise":15.0,"etape":"ATTENTE_ACHAT","qty":0.0,"gain_cumule":0.0,"cycles":0})
        save_config(st.session_state.bots); st.rerun()

st.divider()
for m in reversed(st.session_state.logs[-10:]): st.write(m)
