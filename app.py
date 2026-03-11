import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

# 1. CONFIGURATION PAGE
st.set_page_config(page_title="XRP SNIPER BUILDER", layout="wide")
symbol = "XRP/USDC"
st_autorefresh(interval=40000, key="bot_refresh")

# Initialisation
if "pending_orders" not in st.session_state: st.session_state.pending_orders = set()
if "logs" not in st.session_state: st.session_state.logs = []
if "run" not in st.session_state: st.session_state.run = False
if "bots" not in st.session_state: st.session_state.bots = {}

def log(msg): 
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# 2. CONNEXION KRAKEN
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"], 
        "secret": st.secrets["KRAKEN_API_SECRET"], 
        "enableRateLimit": True
    })
exchange = get_exchange()

# 3. BOUCLE DE TRADING
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol, params={'nonce': str(int(time.time()*1000))})
        price = (ticker["bid"] + ticker["ask"]) / 2
        st.session_state.price = price
        bal = exchange.fetch_balance()
        st.session_state.usdc = bal["free"].get("USDC", 0.0)
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
        log(f"🎯 Flux : {price:.5f}")
    except: price = st.session_state.get("price", 0)

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot.get("actif") or i in st.session_state.pending_orders: continue
        mise_actu = bot.get("mise", 15.0) + bot.get("gain_cumule", 0.0)
        
        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            if st.session_state.get("usdc", 0) >= mise_actu:
                st.session_state.pending_orders.add(i)
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot.update({"qty": qty, "etape": "ATTENTE_VENTE"})
                    log(f"🟢 Bot {i} : ACHAT OK")
                finally: st.session_state.pending_orders.discard(i)
        
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            if bot["qty"] > 0:
                st.session_state.pending_orders.add(i)
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - mise_actu
                    bot.update({"gain_cumule": bot["gain_cumule"] + gain, "cycles": bot.get("cycles",0)+1, "qty": 0, "etape": "ATTENTE_ACHAT"})
                    log(f"💰 Bot {i} : VENTE OK (+{gain:.2f}$)")
                finally: st.session_state.pending_orders.discard(i)

run_cycle()

# 4. INTERFACE
st.title("🚀 Mon Armée de Snipers")

with st.sidebar:
    st.header("➕ Ajouter un Bot")
    id_bot = st.number_input("Numéro du Bot", min_value=1, max_value=100, value=1)
    b_exist = st.session_state.bots.get(id_bot, {"p_achat": 1.35, "p_vente": 1.38, "mise": 15.0})
    
    n_a = st.number_input("Prix Achat", value=float(b_exist["p_achat"]), format="%.4f", key=f"a{id_bot}")
    n_v = st.number_input("Prix Vente", value=float(b_exist["p_vente"]), format="%.4f", key=f"v{id_bot}")
    n_m = st.number_input("Mise ($)", value=float(b_exist["mise"]), key=f"m{id_bot}")
    
    if st.button("➕ AJOUTER / MODIFIER"):
        st.session_state.bots[id_bot] = {
            "id": id_bot, "actif": False, "p_achat": n_a, "p_vente": n_v,
            "mise": n_m, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0
        }
        st.rerun()
    
    st.divider()
    if st.button("🚀 START TOUT"): st.session_state.run = True; st.rerun()
    if st.button("🛑 STOP TOUT"): st.session_state.run = False; st.rerun()

# METRICS
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price',0):.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc',0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp',0):.2f}")

st.divider()

# AFFICHAGE DU TABLEAU
if not st.session_state.bots:
    st.info("💡 Ta liste est vide. Utilise la barre latérale pour ajouter ton premier Bot !")
else:
    st.subheader(f"📊 Bots Actifs ({len(st.session_state.bots)})")
    h = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.5, 0.5])
    h[0].write("**ID**"); h[1].write("**St**"); h[2].write("**Achat**")
    h[3].write("**Vente**"); h[4].write("**Mise**"); h[5].write("**Gain**")
    h[6].write("**Qty**"); h[7].write("**Étape**"); h[8].write("**Cy**")
    h[9].write("**Go**"); h[10].write("**Supp**")

    for i in sorted(st.session_state.bots.keys()):
        bt = st.session_state.bots[i]
        r = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.5, 0.5])
        
        r[0].write(f"#{i}")
        r[1].write("✅" if bt["actif"] else "⚪")
        r[2].write(f"{bt['p_achat']:.3f}")
        r[3].write(f"{bt['p_vente']:.3f}")
        r[4].write(f"{bt['mise'] + bt['gain_cumule']:.1f}$")
        
        g = bt["gain_cumule"]
        color = "green" if g > 0 else "white"
        r[5].markdown(f":{color}[{g:.2f}$]")
        r[6].write(f"{bt['qty']:.1f}")
        
        icon = "🔵" if "ACHAT" in bt["etape"] else "🟢"
        r[7].write(f"{icon} {bt['etape'][:6]}")
        r[8].write(str(bt.get("cycles", 0)))
        
        if r[9].button("🚀" if not bt["actif"] else "🛑", key=f"btn{i}"):
            st.session_state.bots[i]["actif"] = not bt["actif"]
            st.rerun()
        if r[10].button("🗑️", key=f"del{i}"):
            del st.session_state.bots[i]
            st.rerun()

st.divider()
for m in reversed(st.session_state.logs[-10:]):
    st.write(m)
