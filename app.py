import streamlit as st
import ccxt
import pandas as pd
import time
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP SNIPER IMMORTAL", layout="wide")
symbol = "XRP/USDC"
st_autorefresh(interval=40000, key="bot_refresh")

# Initialisation des logs et verrous
if "pending_orders" not in st.session_state: st.session_state.pending_orders = set()
if "logs" not in st.session_state: st.session_state.logs = []

# --- 2. KRAKEN ---
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True
    })
exchange = get_exchange()

# --- 3. INITIALISATION (MODIFIE TES BOTS ICI SUR GITHUB POUR LE REBOOT) ---
# Change "actif": False en "actif": True pour qu'ils soient ON au démarrage
if "bots" not in st.session_state:
    st.session_state.bots = {
        1: {"id": 1, "actif": True, "p_achat": 1.320, "p_vente": 1.350, "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0},
        2: {"id": 2, "actif": True, "p_achat": 1.350, "p_vente": 1.380, "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0},
        3: {"id": 3, "actif": False, "p_achat": 1.380, "p_vente": 1.420, "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0},
        4: {"id": 4, "actif": False, "p_achat": 1.420, "p_vente": 1.450, "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0},
        5: {"id": 5, "actif": False, "p_achat": 1.389, "p_vente": 1.39, "mise": 10.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0},
        6: {"id": 6, "actif": False, "p_achat": 1.38, "p_vente": 1.39, "mise": 10.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0},

    }

# Force le moteur sur "START" au démarrage
if "run" not in st.session_state: 
    st.session_state.run = True 

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# --- 4. BOUCLE DE TRADING ---
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol, params={'nonce': str(int(time.time()*1000))})
        price = (ticker["bid"] + ticker["ask"]) / 2
        st.session_state.price = price
        bal = exchange.fetch_balance()
        st.session_state.usdc = bal['free'].get('USDC', 0.0)
        st.session_state.xrp = bal['free'].get('XRP', 0.0)
        log(f"🎯 Flux : {price:.5f}")
    except: price = st.session_state.get("price", 0)

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot.get("actif") or i in st.session_state.pending_orders: continue
        mise_actu = bot["mise"] + bot["gain_cumule"]

        # ACHAT
        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            if st.session_state.get("usdc", 0) >= mise_actu:
                st.session_state.pending_orders.add(i)
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot.update({"qty": qty, "etape": "ATTENTE_VENTE"})
                    log(f"🟢 Bot {i} : ACHAT {qty:.1f} XRP")
                finally: st.session_state.pending_orders.discard(i)

        # VENTE
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            if bot["qty"] > 0:
                st.session_state.pending_orders.add(i)
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - mise_actu
                    bot.update({"gain_cumule": bot["gain_cumule"] + gain, "cycles": bot.get("cycles",0)+1, "qty": 0, "etape": "ATTENTE_ACHAT"})
                    log(f"💰 Bot {i} : VENTE (+{gain:.2f}$)")
                finally: st.session_state.pending_orders.discard(i)

run_cycle()

# --- 5. INTERFACE ---
st.title("🚀 Sniper Immortel XRP")
st.caption(f"Dernier rafraîchissement : {time.strftime('%H:%M:%S')}")

with st.sidebar:
    st.header("⚙️ Contrôle")
    if st.button("🚀 START TOUT"): st.session_state.run = True; st.rerun()
    if st.button("🛑 STOP TOUT"): st.session_state.run = False; st.rerun()
    st.divider()
    st.info("💡 Pour changer les prix ou l'activation au démarrage, modifie le fichier app.py sur GitHub.")

# METRICS
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price',0):.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc',0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp',0):.2f}")

st.divider()

# TABLEAU INDEXÉ
h = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.6])
h[0].write("**ID**"); h[1].write("**St**"); h[2].write("**Achat**")
h[3].write("**Vente**"); h[4].write("**Mise**"); h[5].write("**Gain**")
h[6].write("**Qty**"); h[7].write("**Étape**"); h[8].write("**Cy**"); h[9].write("**Go**")

for i in sorted(st.session_state.bots.keys()):
    bt = st.session_state.bots[i]
    r = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.6])
    
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

st.divider()
for m in reversed(st.session_state.logs[-10:]):
    st.write(m)


