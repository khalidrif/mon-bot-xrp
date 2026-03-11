import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="XRP Sniper REAL TRADING", layout="wide")
symbol = "XRP/USDC"

# Connexion Google Sheets (Disque dur)
conn = st.connection("gsheets", type=GSheetsConnection)

# FORCER LE RAFRAÎCHISSEMENT TOUTES LES 30 SECONDES
st_autorefresh(interval=30000, key="bot_refresh")

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# 2. CONNEXION KRAKEN (SANS CACHE)
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
exchange = get_exchange()

# 3. CHARGEMENT / SAUVEGARDE CLOUD
def load_config():
    try:
        df = conn.read(ttl=1) # On force la lecture fraîche
        bots = {}
        for _, row in df.iterrows():
            bots[int(row['id'])] = {
                "id": int(row['id']), "actif": bool(row['actif']),
                "p_achat": float(row['p_achat']), "p_vente": float(row['p_vente']),
                "mise": float(row['mise']), "etape": str(row['etape']),
                "qty": float(row['qty']), "gain_cumule": float(row['gain_cumule'])
            }
        return bots
    except: return None

def save_config(bots_dict):
    try:
        data = [{"id": i, **b} for i, b in bots_dict.items()]
        df = pd.DataFrame(data)
        conn.update(data=df)
    except: st.error("❌ Erreur Sauvegarde Google Sheets")

# 4. INITIALISATION
if "bots" not in st.session_state:
    cfg = load_config()
    if cfg: st.session_state.bots = cfg
    else: st.stop()

if "run" not in st.session_state: st.session_state.run = False

# 5. BOUCLE DE TRADING (PRIX NERVEUX SANS CACHE)
def run_cycle():
    try:
        # On demande le ticker frais (Bid/Ask) pour voir le prix bouger
        ticker = exchange.fetch_ticker(symbol)
        
        # CALCUL DU PRIX MOYEN (Plus précis que 'last')
        price = (ticker["bid"] + ticker["ask"]) / 2
        st.session_state.price = price
        
        # LOGS DU PRIX
        log(f"⚡ Prix Marché : {price:.5f}")
        
        # Mise à jour des soldes
        bal = exchange.fetch_balance()
        usdc_dispo = bal["free"].get("USDC", 0.0)
        st.session_state.usdc = usdc_dispo
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
    except Exception as e:
        log(f"⚠️ Erreur Flux API : {str(e)[:30]}")
        price = st.session_state.get("price", 0)
        usdc_dispo = st.session_state.get("usdc", 0)

    # EXECUTION DES ORDRES SI LE BOUTON EST SUR "RUN"
    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        if not bot["actif"]: continue
        
        # LOGIQUE ACHAT
        if bot["etape"] == "ATTENTE_ACHAT" and price <= bot["p_achat"]:
            if usdc_dispo >= bot["mise"]:
                try:
                    qty = float(exchange.amount_to_precision(symbol, (bot["mise"] * 0.98) / price))
                    exchange.create_market_buy_order(symbol, qty)
                    bot["qty"] = qty
                    bot["etape"] = "ATTENTE_VENTE"
                    save_config(st.session_state.bots)
                    log(f"🟢 BOT {i} : ACHAT de {qty} XRP réalisé")
                except Exception as e: log(f"❌ Erreur Achat Bot {i}")

        # LOGIQUE VENTE
        elif bot["etape"] == "ATTENTE_VENTE" and price >= bot["p_vente"]:
            if bot["qty"] > 0:
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    bot["gain_cumule"] += (price * qty_sell) - bot["mise"]
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"🔴 BOT {i} : VENTE réalisée")
                except Exception as e: log(f"❌ Erreur Vente Bot {i}")

run_cycle()

# 6. INTERFACE UTILISATEUR (UI)
st.title("🚀 XRP Sniper REAL TRADING")
st.caption("Flux 30s | Connexion Google Sheets | Trading Actif")

with st.sidebar:
    st.header("⚙️ Config")
    id_bot = st.selectbox("Sélectionner Bot", range(1, 51))
    b = st.session_state.bots[id_bot]
    b["actif"] = st.toggle("Activer le Bot", b["actif"])
    b["p_achat"] = st.number_input("Prix Achat", value=b["p_achat"], format="%.4f")
    b["p_vente"] = st.number_input("Prix Vente", value=b["p_vente"], format="%.4f")
    b["mise"] = st.number_input("Mise ($)", value=b["mise"])
    if st.button("💾 Sauvegarder sur Cloud"):
        save_config(st.session_state.bots)
        st.success("Config enregistrée !")
    st.divider()
    if st.button("🚀 DÉMARRER TOUT", use_container_width=True): st.session_state.run = True
    if st.button("🛑 STOP TOUT", use_container_width=True): st.session_state.run = False

# METRICS
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price', 0):.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc', 0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp', 0):.2f}")

# TABLEAU DES BOTS
st.divider()
st.subheader("📊 État des 50 Bots")
titres = st.columns([0.5, 1, 1, 1, 1.5, 1])
titres.write("**ID**"); titres.write("**Status**"); titres.write("**Achat**")
titres.write("**Vente**"); titres.write("**Étape**"); titres.write("**Gain**")

for i in range(1, 51):
    bt = st.session_state.bots.get(i)
    if not bt: continue
    row = st.columns([0.5, 1, 1, 1, 1.5, 1])
    row.write(f"#{i}")
    row.write("✅" if bt["actif"] else "⚪")
    row.write(f"{bt['p_achat']:.4f}")
    row.write(f"{bt['p_vente']:.4f}")
    icon = "🔵" if "ACHAT" in bt["etape"] else "🟢"
    row.write(f"{icon} {bt['etape']}")
    row.write(f"{bt['gain_cumule']:.2f}$")

# LOGS
st.divider()
st.subheader("📜 Logs de Trading")
for m in reversed(st.session_state.logs[-15:]): st.write(m)
