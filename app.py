import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_gsheets import GSheetsConnection

# ------------------------------------------------------------
# CONFIG DE BASE
# ------------------------------------------------------------
st.set_page_config(page_title="XRP SNIPER 50 BOTS", layout="wide")
symbol = "XRP/USDC"
conn = st.connection("gsheets", type=GSheetsConnection)
st_autorefresh(interval=40000, key="bot_refresh")

# ------------------------------------------------------------
# VARIABLES DE SESSION PERSISTANTES
# ------------------------------------------------------------
if "pending_orders" not in st.session_state: st.session_state.pending_orders = set()
if "logs" not in st.session_state: st.session_state.logs = []
if "run" not in st.session_state: st.session_state.run = False
st.session_state.setdefault("price", 0.0)
st.session_state.setdefault("usdc", 0.0)
st.session_state.setdefault("xrp", 0.0)

# ------------------------------------------------------------
# LOG AVEC HISTORIQUE LIMITÉ (200 LIGNES MAX)
# ------------------------------------------------------------
def log(msg):
    entry = f"{time.strftime('%H:%M:%S')} | {msg}"
    st.session_state.logs.append(entry)
    if len(st.session_state.logs) > 200:
        st.session_state.logs = st.session_state.logs[-200:]

# ------------------------------------------------------------
# CONNEXION A KRAKEN
# ------------------------------------------------------------
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
exchange = get_exchange()

# ------------------------------------------------------------
# LECTURE / SAUVEGARDE CONFIG SUR GOOGLE SHEETS
# ------------------------------------------------------------
def load_config():
    try:
        df = conn.read(ttl=0)
        if df.empty:
            return {}
        return {int(row['id']): row.to_dict() for _, row in df.iterrows()}
    except Exception:
        return {}

def save_config(bots_dict):
    try:
        df_to_save = pd.DataFrame(list(bots_dict.values()))
        conn.update(data=df_to_save)
        st.toast("✅ Cloud Sync OK")
    except Exception as e:
        st.error(f"❌ Erreur Sync : {e}")

# ------------------------------------------------------------
# INITIALISATION DES 50 BOTS
# ------------------------------------------------------------
if "bots" not in st.session_state or not st.session_state.bots:
    cfg = load_config()
    all_bots = {}
    for i in range(1, 51):
        if cfg and i in cfg:
            all_bots[i] = cfg[i]
        else:
            all_bots[i] = {
                "id": i,
                "actif": False,
                "p_achat": 1.35,
                "p_vente": 1.38,
                "mise": 15.0,
                "etape": "ATTENTE_ACHAT",
                "qty": 0.0,
                "gain_cumule": 0.0,
                "cycles": 0,
            }
    st.session_state.bots = all_bots

# ------------------------------------------------------------
# LOGIQUE DU BOT : RUN_CYCLE
# ------------------------------------------------------------
def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol, params={'nonce': str(int(time.time()*1000))})
        price = (ticker["bid"] + ticker["ask"]) / 2
        st.session_state.price = price
        bal = exchange.fetch_balance()
        st.session_state.usdc = bal["free"].get("USDC", 0.0)
        st.session_state.xrp = bal["free"].get("XRP", 0.0)
        log(f"⚡ Prix Marché : {price:.5f}")
    except Exception:
        price = st.session_state.get("price", 0)

    if not st.session_state.run:
        return

    usdc_dispo = st.session_state.usdc

    for i, bot in st.session_state.bots.items():
        if not bot.get("actif") or i in st.session_state.pending_orders:
            continue

        mise_actu = bot.get("mise", 15.0) + bot.get("gain_cumule", 0.0)
        etape = bot["etape"]

        log(f"🤖 Bot {i} | {etape} | Achat={bot['p_achat']:.4f} | Vente={bot['p_vente']:.4f}")

        # ---- ATTENTE_ACHAT ----
        if etape == "ATTENTE_ACHAT":
            if price <= bot["p_achat"]:
                log(f"🟢 Condition ACHAT OK  → {price:.5f} <= {bot['p_achat']:.5f}")
                if usdc_dispo >= mise_actu:
                    st.session_state.pending_orders.add(i)
                    try:
                        qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                        exchange.create_market_buy_order(symbol, qty)
                        bot.update({"qty": qty, "etape": "ATTENTE_VENTE"})
                        save_config(st.session_state.bots)
                        log(f"✅ Bot {i} ACHAT executé qty={qty:.2f}")
                    except Exception as e:
                        log(f"❌ Bot {i} Erreur Achat : {e}")
                    finally:
                        st.session_state.pending_orders.discard(i)
                else:
                    log(f"⚠️ Solde insuffisant USDC {usdc_dispo:.2f}/{mise_actu:.2f}")
            else:
                log(f"⏳ Bot {i} attend ACHAT : prix {price:.5f} > {bot['p_achat']:.5f}")

        # ---- ATTENTE_VENTE ----
        elif etape == "ATTENTE_VENTE":
            if price >= bot["p_vente"]:
                log(f"🟣 Condition VENTE OK  → {price:.5f} >= {bot['p_vente']:.5f}")
                st.session_state.pending_orders.add(i)
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_market_sell_order(symbol, qty_sell)
                    gain = (price * qty_sell) - mise_actu
                    bot.update({
                        "gain_cumule": bot["gain_cumule"] + gain,
                        "cycles": bot.get("cycles", 0) + 1,
                        "qty": 0.0,
                        "etape": "ATTENTE_ACHAT",
                    })
                    save_config(st.session_state.bots)
                    log(f"💰 Bot {i} VENTE executée +{gain:.2f}$")
                except Exception as e:
                    log(f"❌ Bot {i} Erreur Vente : {e}")
                finally:
                    st.session_state.pending_orders.discard(i)
            else:
                log(f"⏳ Bot {i} attend VENTE : prix {price:.5f} < {bot['p_vente']:.5f}")

run_cycle()

# ------------------------------------------------------------
# INTERFACE STREAMLIT
# ------------------------------------------------------------
st.title("🚀 SNIPER 50 BOTS CONTROL")

with st.sidebar:
    id_bot = st.selectbox("Bot #", range(1, 51), key="bot_select_sidebar")
    b = st.session_state.bots[id_bot]
    n_a = st.number_input("Achat", value=float(b["p_achat"]), format="%.4f", key=f"a{id_bot}")
    n_v = st.number_input("Vente", value=float(b["p_vente"]), format="%.4f", key=f"v{id_bot}")
    n_m = st.number_input("Mise", value=float(b["mise"]), key=f"m{id_bot}")
    if st.button("💾 SAUVEGARDER", key=f"save_{id_bot}"):
        st.session_state.bots[id_bot].update({"p_achat": n_a, "p_vente": n_v, "mise": n_m})
        save_config(st.session_state.bots)
        st.rerun()
    if st.button("🚀 START TOUT", key="start_all"):
        st.session_state.run = True
        st.rerun()
    if st.button("🛑 STOP TOUT", key="stop_all"):
        st.session_state.run = False
        st.rerun()

# ------------------------------------------------------------
# MÉTRIQUES GLOBAL BALANCE
# ------------------------------------------------------------
m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{float(st.session_state.get('price',0) or 0):.5f}")
m2.metric("USDC", f"{float(st.session_state.get('usdc',0) or 0):.2f}$")
m3.metric("XRP", f"{float(st.session_state.get('xrp',0) or 0):.2f}")

# ------------------------------------------------------------
# TABLEAU BOTS
# ------------------------------------------------------------
st.divider()
hdr = st.columns([0.5,0.5,0.8,0.8,0.8,0.6,1.2,0.5,0.6,0.6,1])
for c,t in zip(hdr,["**ID**","**St**","**Achat**","**Vente**","**Mise**","**Qty**","**Étape**","**Cy**","**Go**","**Supp**","**Gain**"]):
    c.write(t)

for i in sorted(st.session_state.bots.keys()):
    bt = st.session_state.bots[i]
    r = st.columns([0.5,0.5,0.8,0.8,0.8,0.6,1.2,0.5,0.6,0.6,1])
    r[0].write(f"#{i}")
    r[1].write("✅" if bt["actif"] else "⚪")
    r[2].write(f"{bt['p_achat']:.3f}")
    r[3].write(f"{bt['p_vente']:.3f}")
    r[4].write(f"{bt['mise']+bt['gain_cumule']:.1f}$")
    r[5].write(f"{bt['qty']:.1f}")
    r[6].write(f"{'🔵' if 'ACHAT' in bt['etape'] else '🟢'} {bt['etape'][:6]}")
    r[7].write(str(bt.get('cycles',0)))

    if r[8].button("🚀" if not bt["actif"] else "🛑", key=f"go{i}"):
        st.session_state.bots[i]["actif"] = not bt["actif"]
        save_config(st.session_state.bots)
        st.rerun()

    if r[9].button("🗑️", key=f"del{i}"):
        st.session_state.bots[i].update({
            "actif":False,"p_achat":1.35,"p_vente":1.38,
            "mise":15.0,"etape":"ATTENTE_ACHAT","qty":0.0,
            "gain_cumule":0.0,"cycles":0
        })
        save_config(st.session_state.bots)
        st.rerun()

    g = bt["gain_cumule"]
    couleur = "green" if g > 0 else "white"
    r[10].markdown(f":{couleur}[{g:.2f}$]")

# ------------------------------------------------------------
# LOGS RÉCENTS
# ------------------------------------------------------------
st.divider()
st.subheader("📝 Logs en direct")
for m in reversed(st.session_state.logs[-20:]):
    st.write(m)
