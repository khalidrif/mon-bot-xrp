import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP SNIPER FINAL", layout="wide")
symbol = "XRP/USDC"

# Connexion Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Erreur de connexion Google Sheets : {e}")
    st.stop()

# Auto-refresh
st_autorefresh(interval=40000, key="bot_refresh")

if "logs" not in st.session_state: st.session_state.logs = []
if "pending_orders" not in st.session_state: st.session_state.pending_orders = set()

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# --- 2. KRAKEN ---
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
exchange = get_exchange()

# --- 3. CLOUD FUNCTIONS (SIMPLIFIÉES) ---
def load_config():
    try:
        # ttl=0 pour éviter le cache
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
    except Exception as e:
        st.warning(f"⚠️ Lecture Cloud impossible : {e}")
        return {}

def save_config(bots_dict):
    try:
        # On prépare les données proprement
        df_to_save = pd.DataFrame(list(bots_dict.values()))
        conn.update(data=df_to_save)
        st.success("✅ Sauvegardé sur Google Sheets !")
        time.sleep(1) # Petit délai pour laisser Google enregistrer
    except Exception as e:
        st.error(f"❌ Erreur Sauvegarde : {e}")

# --- 4. INITIALISATION ---
if "bots" not in st.session_state or not st.session_state.bots:
    st.session_state.bots = load_config()

if "run" not in st.session_state: st.session_state.run = False

# --- 5. LOGIQUE TRADING ---
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = (ticker["bid"] + ticker["ask"]) / 2
        st.session_state.price = price
        log(f"🎯 Prix Marché : {price:.5f}")
    except:
        price = st.session_state.get("price", 0)

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot.get("actif") or i in st.session_state.pending_orders: continue
        
        mise_actu = bot.get("mise", 15.0) + bot.get("gain_cumule", 0.0)

        # ACHAT
        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            st.session_state.pending_orders.add(i)
            try:
                qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                exchange.create_market_buy_order(symbol, qty)
                bot["qty"] = qty
                bot["etape"] = "ATTENTE_VENTE"
                save_config(st.session_state.bots)
                log(f"🟢 Bot {i} : ACHAT {qty:.2f}")
            finally: st.session_state.pending_orders.discard(i)

        # VENTE
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            st.session_state.pending_orders.add(i)
            try:
                qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                exchange.create_market_sell_order(symbol, qty_sell)
                gain = (price * qty_sell) - mise_actu
                bot["gain_cumule"] += gain
                bot["qty"] = 0
                bot["etape"] = "ATTENTE_ACHAT"
                save_config(st.session_state.bots)
                log(f"💰 Bot {i} : VENTE +{gain:.2f}$")
            finally: st.session_state.pending_orders.discard(i)

run_cycle()

# --- 6. INTERFACE ---
st.title("🚀 SNIPER PRO CONTROL")

with st.sidebar:
    st.header("⚙️ Configuration")
    id_bot = st.selectbox("Sélectionner Bot", range(1, 51))
    b = st.session_state.bots.get(id_bot, {"p_achat": 1.35, "p_vente": 1.38, "mise": 15.0})
    
    n_a = st.number_input("Achat", value=float(b["p_achat"]), format="%.4f", key=f"na_{id_bot}")
    n_v = st.number_input("Vente", value=float(b["p_vente"]), format="%.4f", key=f"nv_{id_bot}")
    n_m = st.number_input("Mise ($)", value=float(b["mise"]), key=f"nm_{id_bot}")
    
    if st.button("💾 SAUVEGARDER"):
        if id_bot not in st.session_state.bots:
            st.session_state.bots[id_bot] = {"id":id_bot, "actif":False, "etape":"ATTENTE_ACHAT", "qty":0.0, "gain_cumule":0.0, "cycles":0}
        st.session_state.bots[id_bot].update({"p_achat": n_a, "p_vente": n_v, "mise": n_m})
        save_config(st.session_state.bots)
        st.rerun()

    if st.button("🚀 START TOUT"): st.session_state.run = True; st.rerun()
    if st.button("🛑 STOP TOUT"): st.session_state.run = False; st.rerun()

# Metrics
p_val = st.session_state.get("price", 0)
st.metric("Prix XRP", f"{p_val:.5f}")

# Tableau
st.divider()
st.subheader("📊 État des Bots")
cols = st.columns([0.5, 0.5, 1, 1, 1, 1.5, 0.8, 0.8, 1])
cols[0].write("**ID**"); cols[1].write("**St**"); cols[2].write("**Achat**")
cols[3].write("**Vente**"); cols[4].write("**Mise**"); cols[5].write("**Étape**")
cols[6].write("**Go**"); cols[7].write("**Supp**"); cols[8].write("**Gain**")

for i in sorted(st.session_state.bots.keys()):
    bt = st.session_state.bots[i]
    r = st.columns([0.5, 0.5, 1, 1, 1, 1.5, 0.8, 0.8, 1])
    r[0].write(f"#{i}")
    r[1].write("✅" if bt["actif"] else "⚪")
    r[2].write(f"{bt['p_achat']:.3f}")
    r[3].write(f"{bt['p_vente']:.3f}")
    r[4].write(f"{bt['mise'] + bt['gain_cumule']:.1f}$")
    
    icon = "🔵" if "ACHAT" in bt["etape"] else "🟢"
    r[5].write(f"{icon} {bt['etape'][:6]}")
    
    if r[6].button("🚀" if not bt["actif"] else "🛑", key=f"b_{i}"):
        st.session_state.bots[i]["actif"] = not bt["actif"]
        save_config(st.session_state.bots); st.rerun()
            
    if r[7].button("🗑️", key=f"d_{i}"):
        del st.session_state.bots[i]
        save_config(st.session_state.bots); st.rerun()

    r[8].write(f"{bt['gain_cumule']:.2f}$")

st.divider()
for m in reversed(st.session_state.logs[-10:]): st.write(m)
