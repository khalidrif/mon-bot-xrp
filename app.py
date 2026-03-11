import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION PAGE
st.set_page_config(page_title="XRP SNIPER CLOUD PRO", layout="wide")
symbol = "XRP/USDC"
conn = st.connection("gsheets", type=GSheetsConnection)

# RAFRAÎCHISSEMENT AUTO : On passe à 40s pour laisser le Cloud respirer
st_autorefresh(interval=40000, key="bot_refresh")

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# 2. CONNEXION KRAKEN (SÉCURISÉE)
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
exchange = get_exchange()

# 3. FONCTIONS CLOUD (FORCE BRUTE SANS CACHE)
def load_config():
    try:
        # ttl=0 force Google Sheets à donner la version la plus récente possible
        df = conn.read(ttl=0) 
        bots = {}
        for _, row in df.iterrows():
            idx = int(row['id'])
            bots[idx] = {
                "id": idx, "actif": bool(row['actif']),
                "p_achat": float(row['p_achat']), "p_vente": float(row['p_vente']),
                "mise": float(row['mise']), "etape": str(row['etape']),
                "qty": float(row.get('qty', 0)), "gain_cumule": float(row.get('gain_cumule', 0)),
                "cycles": int(row.get('cycles', 0))
            }
        return bots
    except:
        return st.session_state.get("bots")

def save_config(bots_dict):
    try:
        data = [v for k, v in bots_dict.items()]
        df = pd.DataFrame(data)
        conn.update(data=df)
        st.toast("✅ Sauvegardé sur Google Sheets !")
    except:
        st.error("❌ Erreur de synchronisation Cloud")

# 4. INITIALISATION
if "bots" not in st.session_state:
    cfg = load_config()
    if cfg: st.session_state.bots = cfg
    else: st.stop()

if "run" not in st.session_state: st.session_state.run = False

# 5. BOUCLE DE TRADING (PRIX EN DIRECT)
def run_cycle():
    try:
        # On ajoute un 'nonce' pour forcer Kraken à ignorer son cache interne
        ticker = exchange.fetch_ticker(symbol, params={'nonce': str(int(time.time()*1000))})
        price = (ticker["bid"] + ticker["ask"]) / 2
        st.session_state.price = price
        
        bal = exchange.fetch_balance()
        st.session_state.usdc = bal["free"].get("USDC", 0.0)
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
        
        log(f"🎯 Flux Direct : {price:.5f}")
    except Exception as e:
        log(f"⚠️ Erreur Flux : {str(e)[:20]}")
        price = st.session_state.get("price", 0)

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot.get("actif", False): continue
        mise_actu = bot.get("mise", 15.0) + bot.get("gain_cumule", 0.0)

        # LOGIQUE SNIPER
        if bot.get("etape") == "ATTENTE_ACHAT" and price <= bot.get("p_achat"):
            try:
                qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                exchange.create_market_buy_order(symbol, qty)
                bot["qty"] = qty; bot["etape"] = "ATTENTE_VENTE"
                save_config(st.session_state.bots); log(f"🟢 Bot {i} : ACHAT {qty} XRP")
            except: pass
        
        elif bot.get("etape") == "ATTENTE_VENTE" and price >= bot.get("p_vente"):
            if bot.get("qty", 0) > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - mise_actu
                    bot["gain_cumule"] += gain; bot["cycles"] = bot.get("cycles", 0) + 1
                    bot["qty"] = 0; bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots); log(f"💰 Bot {i} : VENTE +{gain:.2f}$")
                except: pass

run_cycle()

# 6. INTERFACE (UI)
st.title("🚀 XRP SNIPER - MODE DIRECT")
st.caption(f"Dernière mise à jour : {time.strftime('%H:%M:%S')} (40s interval)")

with st.sidebar:
    st.header("⚙️ Réglages")
    id_bot = st.selectbox("Choisir Bot", range(1, 51))
    b = st.session_state.bots.get(id_bot)
    
    # On utilise des 'keys' uniques pour éviter les conflits de saisie
    new_achat = st.number_input("Prix Achat", value=b["p_achat"], format="%.4f", key=f"in_a_{id_bot}")
    new_vente = st.number_input("Prix Vente", value=b["p_vente"], format="%.4f", key=f"in_v_{id_bot}")
    new_mise = st.number_input("Mise ($)", value=b["mise"], key=f"in_m_{id_bot}")
    
    if st.button("💾 SAUVEGARDER & SYNCHRONISER"):
        st.session_state.bots[id_bot]["p_achat"] = new_achat
        st.session_state.bots[id_bot]["p_vente"] = new_vente
        st.session_state.bots[id_bot]["mise"] = new_mise
        save_config(st.session_state.bots)
        st.rerun()

    st.divider()
    if st.button("🚀 START TOUT"): st.session_state.run = True; st.rerun()
    if st.button("🛑 STOP TOUT"): st.session_state.run = False; st.rerun()

# METRICS
p_val = st.session_state.get("price", 0)
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{p_val:.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc', 0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp', 0):.2f}")

# TABLEAU DE CONTRÔLE (INDEXÉ)
st.divider()
st.subheader("📊 Gestion Individuelle")
h = st.columns([0.4, 0.4, 0.8, 0.8, 0.8, 1.2, 0.5, 0.6, 0.6, 1])
h[0].write("**ID**"); h[1].write("**St**"); h[2].write("**Achat**"); h[3].write("**Vente**")
h[4].write("**Mise**"); h[5].write("**Étape**"); h[6].write("**Cy**"); h[7].write("**Go**")
h[8].write("**Clr**"); h[9].write("**Gain**")

for i in range(1, 51):
    bt = st.session_state.bots.get(i)
    if not bt: continue
    r = st.columns([0.4, 0.4, 0.8, 0.8, 0.8, 1.2, 0.5, 0.6, 0.6, 1])
    r[0].write(f"#{i}")
    is_actif = bt.get("actif", False)
    r[1].write("✅" if is_actif else "⚪")
    r[2].write(f"{bt.get('p_achat'):.3f}")
    r[3].write(f"{bt.get('p_vente'):.3f}")
    r[4].write(f"{bt.get('mise') + bt.get('gain_cumule'):.1f}$")
    icon = "🔵" if "ACHAT" in bt.get("etape") else "🟢"
    r[5].write(f"{icon} {bt.get('etape')[:6]}")
    r[6].write(str(bt.get("cycles", 0)))
    
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

    g = bt.get("gain_cumule", 0)
    r[9].markdown(f":{'green' if g > 0 else 'white'}[{g:.2f}$]")

st.divider()
for m in reversed(st.session_state.logs[-10:]): st.write(m)
