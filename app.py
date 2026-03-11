import streamlit as st
import ccxt
import json
import os
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="⚡ XRP Sniper Live Trading", layout="centered")
symbol = "XRP/USDC"
st_autorefresh(interval=20000, key="refresh_trading")
CONFIG_FILE = "bots_config.json"

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# === sauvegarde & chargement ===
def save_bots():
    with open(CONFIG_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=2)
def load_bots():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}

# === Kraken ===
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True
    })
exchange = get_exchange()

# === init bots ===
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()
for b in st.session_state.bots.values():
    b.setdefault("etape", "ACHAT")
    b.setdefault("actif", True)
    b.setdefault("gain_net", 0.0)
    b.setdefault("cycles", 0)
save_bots()

# === prix live ===
try:
    ticker = exchange.fetch_ticker(symbol)
    bid = ticker["bid"]; ask = ticker["ask"]
    mid = (bid + ask) / 2
    log(f"📡 Prix : Bid {bid:.5f} / Ask {ask:.5f}")
except Exception as e:
    bid = ask = mid = 0.0
    log(f"⚠️ Prix erreur : {e}")

st.title("🚀 XRP Sniper Live Trading")
st.metric("Prix XRP", f"{mid:.5f}")
st.caption(f"MAJ : {time.strftime('%H:%M:%S')}")
st.divider()

# === ajouter bot ===
st.subheader("➕ Ajouter un bot")
col1,col2,col3 = st.columns(3)
with col1: p_achat_new = st.number_input("Prix Achat", value=1.390, step=0.0001)
with col2: p_vente_new = st.number_input("Prix Vente", value=1.395, step=0.0001)
with col3: mise_new = st.number_input("Mise ($)", value=10.0, step=1.0)
if st.button("✅ Ajouter"):
    next_id = max(st.session_state.bots.keys())+1 if st.session_state.bots else 1
    st.session_state.bots[next_id] = {"id":next_id,"p_achat":p_achat_new,
        "p_vente":p_vente_new,"mise":mise_new,"etape":"ACHAT","gain_net":0.0,
        "cycles":0,"actif":True}
    save_bots(); log(f"🆕 Bot #{next_id} ajouté"); st.rerun()

# === boucle trading réelle ===
for i,b in st.session_state.bots.items():
    if not b.get("actif"): 
        continue
    try:
        balance = exchange.fetch_balance()
        usdc = float(balance['free'].get('USDC',0))
        qty_precision = exchange.market(symbol)['precision']['amount']
    except:
        continue

    # --- ACHAT réel
    if b["etape"]=="ACHAT" and mid <= b["p_achat"]:
        if usdc >= b["mise"]:
            try:
                qty = round(b["mise"]/b["p_achat"], qty_precision)
                order = exchange.create_limit_buy_order(symbol, qty, b["p_achat"])
                b["etape"]="VENTE"
                log(f"✅ Bot #{i} achat envoyé ({qty} XRP à {b['p_achat']})")
                save_bots()
                st.success(f"Bot #{i} → Achat exécuté ({qty} XRP)")
            except Exception as e:
                log(f"❌ Achat Bot #{i} : {e}")

    # --- VENTE réelle
    elif b["etape"]=="VENTE" and mid >= b["p_vente"]:
        try:
            qty_sell = exchange.amount_to_precision(symbol, qty * 0.995)
            order = exchange.create_limit_sell_order(symbol, float(qty_sell), b["p_vente"])
            gain = (b["p_vente"]-b["p_achat"])/b["p_achat"]*b["mise"]
            b["gain_net"] += gain; b["cycles"] += 1; b["etape"]="ACHAT"; b["mise"] += gain
            log(f"💰 Vente Bot #{i} exécutée +{gain:.2f}$")
            save_bots()
            st.success(f"Vente Bot #{i} exécutée (+{gain:.2f}$)")
        except Exception as e:
            log(f"❌ Vente Bot #{i} : {e}")

# === affichage ===
st.divider()
st.subheader("📊 Mes Bots")
for i,b in sorted(st.session_state.bots.items()):
    couleur="🟢" if b["actif"] else "⚫️"
    if b["actif"] and mid<=b["p_achat"]: couleur="🟡"
    elif b["actif"] and mid>=b["p_vente"]: couleur="🔴"
    st.info(
      f"{couleur} Bot {i} | Achat {b['p_achat']:.4f} | Vente {b['p_vente']:.4f} | "
      f"Mise :{b['mise']:.2f}$ | Gains:{b['gain_net']:.2f}$ | Cycles:{b['cycles']} | Étape:{b['etape']}"
    )

# === logs + prix ===
st.divider()
st.subheader("📜 Historique")
for l in reversed(st.session_state.logs[-12:]): st.write(l)
st.divider()
st.subheader("💹 Prix Kraken")
colA,colB,colC=st.columns(3)
colA.metric("Bid",f"{bid:.5f}"); colB.metric("Ask",f"{ask:.5f}"); colC.metric("Mid",f"{mid:.5f}")
