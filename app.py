import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

# 1. CONFIGURATION
st.set_page_config(page_title="XRP SNIPER IMMORTAL SECRETS", layout="wide")
symbol = "XRP/USDC"
st_autorefresh(interval=40000, key="bot_refresh")

if "pending_orders" not in st.session_state: st.session_state.pending_orders = set()
if "logs" not in st.session_state: st.session_state.logs = []
if "run" not in st.session_state: st.session_state.run = False

def log(msg): st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# 2. CONNEXION KRAKEN
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"], 
        "secret": st.secrets["KRAKEN_API_SECRET"], 
        "enableRateLimit": True
    })
exchange = get_exchange()

# 3. INITIALISATION (LIT LES SECRETS POUR NE JAMAIS PERDRE LES PRIX)
if "bots" not in st.session_state:
    try:
        # On charge les bots configurés dans les Secrets Streamlit
        st.session_state.bots = {int(k): dict(v) for k, v in st.secrets["bots"].items()}
    except:
        st.error("⚠️ Erreur : Aucun bot trouvé dans tes Secrets Streamlit !")
        st.stop()

# 4. BOUCLE DE TRADING (PRIX RÉEL)
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
        
        # ACHAT
        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            st.session_state.pending_orders.add(i)
            try:
                qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                exchange.create_market_buy_order(symbol, qty)
                bot.update({"qty": qty, "etape": "ATTENTE_VENTE"})
                log(f"🟢 Bot {i} : ACHAT OK")
            finally: st.session_state.pending_orders.discard(i)
        
        # VENTE
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            if bot.get("qty", 0) > 0:
                st.session_state.pending_orders.add(i)
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - mise_actu
                    bot.update({"gain_cumule": bot["gain_cumule"] + gain, "cycles": bot.get("cycles",0)+1, "qty": 0, "etape": "ATTENTE_ACHAT"})
                    log(f"💰 Bot {i} : VENTE OK (+{gain:.2f}$)")
                finally: st.session_state.pending_orders.discard(i)

run_cycle()

# 5. INTERFACE
st.title("🚀 Sniper Immortel (Mode Secrets)")
st.caption(f"Dernière mise à jour : {time.strftime('%H:%M:%S')}")

with st.sidebar:
    st.header("⚙️ Contrôle Global")
    if st.button("🚀 START TOUT", use_container_width=True): st.session_state.run = True; st.rerun()
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False; st.rerun()
    st.info("💡 Pour modifier les prix à vie, change les valeurs dans 'Secrets' sur Streamlit.")

# METRICS
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price',0):.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc',0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp',0):.2f}")

st.divider()
# TABLEAU INDEXÉ
h = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.6, 0.6])
titres = ["ID", "St", "Achat", "Vente", "Mise", "Gain", "Qty", "Étape", "Cy", "Go", "Reset"]
for col, t in zip(h, titres): col.write(f"**{t}**")

for i in sorted(st.session_state.bots.keys()):
    bt = st.session_state.bots[i]
    r = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.6, 0.6])
    r.write(f"#{i}"); r.write("✅" if bt["actif"] else "⚪")
    r.write(f"{bt['p_achat']:.3f}"); r.write(f"{bt['p_vente']:.3f}")
    r.write(f"{bt['mise'] + bt['gain_cumule']:.1f}$")
    g = bt["gain_cumule"]
    r.markdown(f":{'green' if g > 0 else 'white'}[{g:.2f}$]")
    r.write(f"{bt['qty']:.1f}")
    icon = "🔵" if "ACHAT" in bt["etape"] else "🟢"
    r.write(f"{icon} {bt['etape'][:6]}")
    r.write(str(bt.get("cycles", 0)))
    
    # Bouton ON/OFF individuel
    if r.button("🚀" if not bt["actif"] else "🛑", key=f"btn{i}"):
        st.session_state.bots[i]["actif"] = not bt["actif"]
        st.rerun()
    
    # Bouton Reset (recharge les prix des Secrets)
    if r.button("🔄", key=f"res{i}"):
        st.session_state.bots[i] = dict(st.secrets["bots"][str(i)])
        st.rerun()

st.divider()
for m in reversed(st.session_state.logs[-10:]): st.write(m)
