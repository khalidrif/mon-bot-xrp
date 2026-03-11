import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIG
st.set_page_config(page_title="XRP SNIPER 50 BOTS", layout="wide")
symbol = "XRP/USDC"
conn = st.connection("gsheets", type=GSheetsConnection)
st_autorefresh(interval=40000, key="bot_refresh")

if "pending_orders" not in st.session_state: st.session_state.pending_orders = set()
if "logs" not in st.session_state: st.session_state.logs = []
if "run" not in st.session_state: st.session_state.run = False

def log(msg): st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

@st.cache_resource
def get_exchange():
    return ccxt.kraken({"apiKey": st.secrets["KRAKEN_API_KEY"], "secret": st.secrets["KRAKEN_API_SECRET"], "enableRateLimit": True})
exchange = get_exchange()

def load_config():
    try:
        df = conn.read(ttl=0)
        if df.empty: return {}
        return {int(row['id']): row.to_dict() for _, row in df.iterrows()}
    except: return {}

def save_config(bots_dict):
    try:
        df_to_save = pd.DataFrame(list(bots_dict.values()))
        conn.update(data=df_to_save)
        st.toast("✅ Cloud Sync OK")
    except: st.error("❌ Erreur Sync")

# INITIALISATION FORCÉE DES 50 BOTS
if "bots" not in st.session_state or not st.session_state.bots:
    cfg = load_config()
    all_bots = {}
    for i in range(1, 51):
        if cfg and i in cfg: all_bots[i] = cfg[i]
        else: all_bots[i] = {"id": i, "actif": False, "p_achat": 1.35, "p_vente": 1.38, "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0}
    st.session_state.bots = all_bots

def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol, params={'nonce': str(int(time.time()*1000))})
        price = (ticker["bid"] + ticker["ask"]) / 2
        st.session_state.price = price
        bal = exchange.fetch_balance()
        usdc_dispo = bal["free"].get("USDC", 0.0)
        st.session_state.usdc = usdc_dispo
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
        log(f"🎯 Flux : {price:.5f}")
    except: price = st.session_state.get("price", 0)

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot.get("actif") or i in st.session_state.pending_orders: continue
        mise_actu = bot.get("mise", 15.0) + bot.get("gain_cumule", 0.0)
        
        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            if usdc_dispo >= mise_actu:
                st.session_state.pending_orders.add(i)
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot.update({"qty": qty, "etape": "ATTENTE_VENTE"})
                    save_config(st.session_state.bots)
                    log(f"🟢 Bot {i} : ACHAT")
                finally: st.session_state.pending_orders.discard(i)
        
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            st.session_state.pending_orders.add(i)
            try:
                qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                exchange.create_market_sell_order(symbol, qty_sell)
                gain = (price * qty_sell) - mise_actu
                bot.update({"gain_cumule": bot["gain_cumule"] + gain, "cycles": bot.get("cycles",0)+1, "qty": 0, "etape": "ATTENTE_ACHAT"})
                save_config(st.session_state.bots)
                log(f"💰 Bot {i} : VENTE +{gain:.2f}$")
            finally: st.session_state.pending_orders.discard(i)

run_cycle()

st.title("🚀 SNIPER 50 BOTS CONTROL")
with st.sidebar:
    id_bot = st.selectbox("Bot #", range(1, 51))
    b = st.session_state.bots[id_bot]
    n_a = st.number_input("Achat", value=float(b["p_achat"]), format="%.4f", key=f"a{id_bot}")
    n_v = st.number_input("Vente", value=float(b["p_vente"]), format="%.4f", key=f"v{id_bot}")
    n_m = st.number_input("Mise", value=float(b["mise"]), key=f"m{id_bot}")
    if st.button("💾 SAUVEGARDER"):
        st.session_state.bots[id_bot].update({"p_achat": n_a, "p_vente": n_v, "mise": n_m})
        save_config(st.session_state.bots)
        st.rerun()
    if st.button("🚀 START TOUT"): st.session_state.run = True; st.rerun()
    if st.button("🛑 STOP TOUT"): st.session_state.run = False; st.rerun()

m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price',0):.5f}")
m2.metric("USDC", f"{st.session_state.get('usdc',0):.2f}$")
m3.metric("XRP", f"{st.session_state.get('xrp',0):.2f}")

st.divider()
h = st.columns([0.5, 0.5, 0.8, 0.8, 0.8, 0.6, 1.2, 0.5, 0.6, 0.6, 1])
h[0].write("**ID**"); h[1].write("**St**"); h[2].write("**Achat**"); h[3].write("**Vente**"); h[4].write("**Mise**"); h[5].write("**Qty**"); h[6].write("**Étape**"); h[7].write("**Cy**"); h[8].write("**Go**"); h[9].write("**Supp**"); h[10].write("**Gain**")

for i in sorted(st.session_state.bots.keys()):
    bt = st.session_state.bots[i]
    r = st.columns([0.5, 0.5, 0.8, 0.8, 0.8, 0.6, 1.2, 0.5, 0.6, 0.6, 1])
    r[0].write(f"#{i}"); r[1].write("✅" if bt["actif"] else "⚪")
    r[2].write(f"{bt['p_achat']:.3f}"); r[3].write(f"{bt['p_vente']:.3f}")
    r[4].write(f"{bt['mise'] + bt['gain_cumule']:.1f}$"); r[5].write(f"{bt['qty']:.1f}")
    r[6].write(f"{'🔵' if 'ACHAT' in bt['etape'] else '🟢'} {bt['etape'][:6]}")
    r[7].write(str(bt.get("cycles", 0)))
    if r[8].button("🚀" if not bt["actif"] else "🛑", key=f"btn{i}"):
        st.session_state.bots[i]["actif"] = not bt["actif"]
        save_config(st.session_state.bots); st.rerun()
    if r[9].button("🗑️", key=f"del{i}"):
        st.session_state.bots[i].update({"actif":False,"p_achat":1.35,"p_vente":1.38,"mise":15.0,"etape":"ATTENTE_ACHAT","qty":0.0,"gain_cumule":0.0,"cycles":0})
        save_config(st.session_state.bots); st.rerun()
    g = bt["gain_cumule"]
    r[10].markdown(f":{'green' if g > 0 else 'white'}[{g:.2f}$]")

st.divider()
for m in reversed(st.session_state.logs[-10:]): st.write(m)
