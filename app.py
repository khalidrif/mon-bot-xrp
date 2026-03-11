import streamlit as st  # <-- CETTE LIGNE ÉTAIT MANQUANTE
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP SNIPER PRO", layout="wide")
symbol = "XRP/USDC"
st_autorefresh(interval=40000, key="bot_refresh")

# Initialisation des logs et du verrou global de sécurité
if "logs" not in st.session_state: st.session_state.logs = []
if "run" not in st.session_state: st.session_state.run = True 
if "lock_global" not in st.session_state: st.session_state.lock_global = False

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

# --- 3. INITIALISATION DES BOTS (MODIFIE ICI SUR GITHUB) ---
if "bots" not in st.session_state:
    st.session_state.bots = {
        1: {"id": 1, "actif": True, "p_achat": 1.320, "p_vente": 1.350, "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0},
        2: {"id": 2, "actif": True, "p_achat": 1.350, "p_vente": 1.380, "mise": 15.0, "etape": "ATTENTE_ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0},
    }

# --- 4. BOUCLE DE TRADING (SÉCURITÉ ANTI-DOUBLE & ORDRE LIMIT) ---
def run_cycle():
    if st.session_state.lock_global: return

    try:
        ticker = exchange.fetch_ticker(symbol, params={'nonce': str(int(time.time()*1000))})
        price = float((ticker["bid"] + ticker["ask"]) / 2)
        st.session_state.price = price
        bal = exchange.fetch_balance()
        usdc_dispo = float(bal['free'].get('USDC', 0.0))
        st.session_state.usdc = usdc_dispo
        st.session_state.xrp = bal['free'].get('XRP', 0.0)
        log(f"🎯 Flux : {price:.5f} | USDC : {usdc_dispo:.2f}$")
    except: return

    if not st.session_state.run: return

    for i in sorted(st.session_state.bots.keys()):
        bot = st.session_state.bots[i]
        if not bot.get("actif") or st.session_state.lock_global: continue
        
        mise_actu = float(bot["mise"] + bot["gain_cumule"])
        p_achat_target = float(bot["p_achat"])
        p_vente_target = float(bot["p_vente"])

        # --- ACHAT LIMIT ---
        if bot["etape"] == "ATTENTE_ACHAT" and price <= p_achat_target:
            if usdc_dispo >= mise_actu:
                st.session_state.lock_global = True 
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / p_achat_target))
                    bot["etape"] = "EXECUTION..." 
                    exchange.create_limit_buy_order(symbol, qty, p_achat_target)
                    bot.update({"qty": qty, "etape": "ATTENTE_VENTE"})
                    log(f"✅ Bot {i} : LIMIT ACHAT à {p_achat_target:.5f}")
                    time.sleep(5) 
                    st.rerun() 
                except:
                    bot["etape"] = "ATTENTE_ACHAT"
                    log(f"❌ Erreur Achat {i}")
                finally: 
                    st.session_state.lock_global = False 
                break 

        # --- VENTE LIMIT ---
        elif bot["etape"] == "ATTENTE_VENTE" and price >= p_vente_target:
            if bot.get("qty", 0) > 0:
                st.session_state.lock_global = True
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    bot["etape"] = "EXECUTION..."
                    exchange.create_limit_sell_order(symbol, qty_sell, p_vente_target)
                    gain = (p_vente_target * qty_sell) - mise_actu
                    bot.update({"gain_cumule": bot["gain_cumule"] + gain, "cycles": bot.get("cycles",0)+1, "qty": 0, "etape": "ATTENTE_ACHAT"})
                    log(f"💰 Bot {i} : LIMIT VENTE à {p_vente_target:.5f}")
                    time.sleep(5)
                    st.rerun()
                except:
                    bot["etape"] = "ATTENTE_VENTE"
                    log(f"❌ Erreur Vente {i}")
                finally: 
                    st.session_state.lock_global = False
                break

run_cycle()

# --- 5. INTERFACE (UI SÉCURISÉE) ---
st.title("🚀 Sniper Pro - Précision LIMIT")
st.caption(f"Dernière mise à jour : {time.strftime('%H:%M:%S')}")

m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price',0):.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc',0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp',0):.2f}")

st.divider()

# TABLEAU AVEC INDEXATION DES COLONNES []
h = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.6])
h[0].write("**ID**")
h[1].write("**St**")
h[2].write("**Achat**")
h[3].write("**Vente**")
h[4].write("**Mise**")
h[5].write("**Gain**")
h[6].write("**Qty**")
h[7].write("**Action**")
h[8].write("**Cy**")
h[9].write("**Go**")

for i in sorted(st.session_state.bots.keys()):
    bt = st.session_state.bots[i]
    r = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.6])
    
    r[0].write(f"#{i}")
    r[1].write("✅" if bt["actif"] else "⚪")
    r[2].write(f"{bt['p_achat']:.3f}")
    r[3].write(f"{bt['p_vente']:.3f}")
    r[4].write(f"{bt['mise'] + bt['gain_cumule']:.1f}$")
    
    g = bt["gain_cumule"]
    if g > 0: r[5].markdown(f"**:green[+{g:.2f}$]**")
    else: r[5].write(f"{g:.2f}$")
        
    r[6].write(f"{bt['qty']:.1f}")
    
    if "ACHAT" in bt["etape"]: r[7].markdown("🟢 **ACHAT**")
    elif "VENTE" in bt["etape"]: r[7].markdown("🟠 **VENTE**")
    else: r[7].write("⌛ ...")
        
    r[8].write(str(bt.get("cycles", 0)))
    
    if r[9].button("🚀" if not bt["actif"] else "🛑", key=f"btn{i}"):
        st.session_state.bots[i]["actif"] = not bt["actif"]
        st.rerun()

st.divider()
for m in reversed(st.session_state.logs[-10:]): st.write(m)
