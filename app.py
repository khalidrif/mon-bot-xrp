import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP SNIPER PRO", layout="wide")
symbol = "XRP/USDC"
st_autorefresh(interval=40000, key="bot_refresh")

# Initialisation des verrous anti-double ordre et logs
if "pending_orders" not in st.session_state: st.session_state.pending_orders = set()
if "logs" not in st.session_state: st.session_state.logs = []
if "run" not in st.session_state: st.session_state.run = True 

def log(msg): st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# --- 2. KRAKEN ---
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"], 
        "secret": st.secrets["KRAKEN_API_SECRET"], 
        "enableRateLimit": True
    })
exchange = get_exchange()

# --- 3. INITIALISATION (MODIFIE TES PRIX ICI SUR GITHUB) ---
if "bots" not in st.session_state:
    st.session_state.bots = {
        1: {"id": 1, "actif": True, "p_achat": 1.320, "p_vente": 1.350, "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0},
        2: {"id": 2, "actif": True, "p_achat": 1.350, "p_vente": 1.380, "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0},
    }

# --- 4. BOUCLE DE TRADING (SÉCURITÉ ANTI-DOUBLE) ---
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
        # Verrou de sécurité : ignore si déjà en cours ou inactif
        if not bot.get("actif") or i in st.session_state.pending_orders: continue
        
        mise_actu = bot["mise"] + bot["gain_cumule"]

        # --- ACHAT (VERT 🟢) ---
        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            if st.session_state.get("usdc", 0) >= mise_actu:
                st.session_state.pending_orders.add(i) # VERROU ACTIVÉ
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot.update({"qty": qty, "etape": "ATTENTE_VENTE"})
                    log(f"🟢 Bot {i} : ACHAT RÉUSSI")
                    time.sleep(2) # PAUSE SÉCURITÉ
                except: log(f"❌ Erreur Achat {i}")
                finally: st.session_state.pending_orders.discard(i) # VERROU LIBÉRÉ

        # --- VENTE (ORANGE 🟠) ---
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            if bot["qty"] > 0:
                st.session_state.pending_orders.add(i) # VERROU ACTIVÉ
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - mise_actu
                    bot.update({"gain_cumule": bot["gain_cumule"] + gain, "cycles": bot.get("cycles",0)+1, "qty": 0, "etape": "ATTENTE_ACHAT"})
                    log(f"💰 Bot {i} : VENTE RÉUSSIE (+{gain:.2f}$)")
                    time.sleep(2) # PAUSE SÉCURITÉ
                except: log(f"❌ Erreur Vente {i}")
                finally: st.session_state.pending_orders.discard(i) # VERROU LIBÉRÉ

run_cycle()

# --- 5. INTERFACE (UI) ---
st.title("🚀 Sniper Pro Immortal")
st.caption(f"Dernier rafraîchissement : {time.strftime('%H:%M:%S')}")

m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price',0):.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc',0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp',0):.2f}")

st.divider()

# TABLEAU INDEXÉ
h = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.6])
h.write("**ID**"); h.write("**St**"); h.write("**Achat**")
h.write("**Vente**"); h.write("**Mise**"); h.write("**Gain**")
h.write("**Qty**"); h.write("**Action**"); h.write("**Cy**"); h.write("**Go**")

for i in sorted(st.session_state.bots.keys()):
    bt = st.session_state.bots[i]
    r = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.6])
    
    r.write(f"#{i}")
    r.write("✅" if bt["actif"] else "⚪")
    r.write(f"{bt['p_achat']:.3f}")
    r.write(f"{bt['p_vente']:.3f}")
    r.write(f"{bt['mise'] + bt['gain_cumule']:.1f}$")
    
    # Gain corrigé (sans texte white)
    g = bt["gain_cumule"]
    if g > 0: r.markdown(f"**:green[+{g:.2f}$]**")
    else: r.write(f"{g:.2f}$")
        
    r.write(f"{bt['qty']:.1f}")
    
    # Action (Achat VERT / Vente ORANGE)
    if "ACHAT" in bt["etape"]:
        r.markdown("🟢 **ACHAT**")
    else:
        r.markdown("🟠 **VENTE**")
        
    r.write(str(bt.get("cycles", 0)))
    
    if r.button("🚀" if not bt["actif"] else "🛑", key=f"btn{i}"):
        st.session_state.bots[i]["actif"] = not bt["actif"]
        st.rerun()

st.divider()
for m in reversed(st.session_state.logs[-10:]): st.write(m)
