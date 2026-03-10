import streamlit as st
import ccxt
import json
import os
import time
import datetime

# ------------------------------------------------------------
# VARIABLES DE SESSION PERSISTANTES
# ------------------------------------------------------------
if "run" not in st.session_state: st.session_state.run=False
if "logs" not in st.session_state: st.session_state.logs=[]
if "trades" not in st.session_state: st.session_state.trades=[]
if "start_time" not in st.session_state: st.session_state.start_time=None
if "trade_count" not in st.session_state: st.session_state.trade_count=0
if "start_capital" not in st.session_state: st.session_state.start_capital=None
if "stop_clicked" not in st.session_state: st.session_state.stop_clicked=False

st.set_page_config(page_title="XRP Sniper Pro", layout="wide")
DB_FILE="config_bots_xrp_secure.json"
symbol="XRP/USDC"

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

def auto_refresh():
    st.markdown("""
        <script>
            setTimeout(function() {
                document.getElementById('refresh_button').click();
            }, 800);
        </script>
    """, unsafe_allow_html=True)
    st.button("refresh", key="refresh_button")
auto_refresh()

def save_trades_json():
    with open("trades_log.json","w") as f:
        json.dump(st.session_state.trades,f,indent=2)
def save_trades_csv():
    with open("trades_log.csv","w") as f:
        f.write("time,bot,type,qty,price,gain\n")
        for t in st.session_state.trades:
            f.write(",".join(str(x) for x in t.values())+"\n")

def save_config(bots):
    try:
        with open("backup_config.json","w") as bkp: json.dump(bots,bkp)
    except: pass
    if not isinstance(bots,dict) or len(bots)==0:
        st.error("🔥 Tentative d'écraser avec fichier vide BLOQUÉE !"); return
    try:
        with open(DB_FILE,"w") as f: json.dump(bots,f)
    except Exception as e: st.error(f"❌ ERREUR SAUVEGARDE : {e}")

def load_config():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE,"r") as f:
                data=json.load(f)
            if not isinstance(data,dict) or len(data)==0: raise ValueError
            return {int(k):v for k,v in data.items()}
        except:
            st.warning("⚠️ Config corrompue → restauration backup…")
            if os.path.exists("backup_config.json"):
                with open("backup_config.json","r") as f: backup=json.load(f)
                st.success("✨ Backup restauré"); return {int(k):v for k,v in backup.items()}
            else: st.error("❌ Aucun backup trouvé"); return None
    return None

def reset_bot(i):
    st.session_state.bots[i]={
        "actif":False,"p_achat":1.35,"p_vente":1.38,"mise":15.0,
        "etape":"ATTENTE_ACHAT","qty":0.0,"cycles":0,
        "gain_cumule":0.0,"order_id":None
    }
    save_config(st.session_state.bots); log(f"Bot #{i} réinitialisé")

if "bots" not in st.session_state:
    cfg=load_config()
    if cfg: st.session_state.bots=cfg
    else:
        st.session_state.bots={i:{
            "actif":False,"p_achat":1.35,"p_vente":1.38,"mise":15.0,
            "etape":"ATTENTE_ACHAT","qty":0.0,"cycles":0,
            "gain_cumule":0.0,"order_id":None} for i in range(1,51)}
        save_config(st.session_state.bots)

for b in st.session_state.bots.values():
    if "order_id" not in b: b["order_id"]=None

@st.cache_resource
def get_exchange():
    ex=ccxt.kraken({
        "apiKey":st.secrets["KRAKEN_API_KEY"],
        "secret":st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit":True})
    ex.load_markets(); return ex
exchange=get_exchange()
st.title("🚀 XRP Sniper Pro – Auto‑Correct + Boule de Neige + %")

# ---- EN‑TÊTE COMPACT ----
gain_total = sum(b["gain_cumule"] for b in st.session_state.bots.values())
if st.session_state.run and st.session_state.start_time:
    elapsed = datetime.datetime.now() - st.session_state.start_time
    h, remainder = divmod(int(elapsed.total_seconds()), 3600)
    m, s = divmod(remainder, 60)
    elapsed_txt = f"{h:02d}:{m:02d}:{s:02d}"
    perf_txt = ""
    if st.session_state.start_capital and st.session_state.start_capital > 0:
        perf = (gain_total / st.session_state.start_capital) * 100
        perf_txt = f"({perf:+.2f} %)"
    st.markdown(
        f"### 🟢 **RUNNING {elapsed_txt}** | 💹 Trades : {st.session_state.trade_count} "
        f"| 💰 Gain : {gain_total:.4f} USDC {perf_txt}"
    )
else:
    st.markdown("### 🔴 **BOTS ARRÊTÉS** | Aucun trade actif")

# ---- SIDEBAR : CONTRÔLES ----
with st.sidebar:
    st.header("⚙️ CONFIG BOT")

    id_bot = st.sidebar.selectbox("Bot n°", range(1, 51), key=f"bot_select_{time.time()}")
    bot = st.session_state.bots[id_bot]

    bot["actif"] = st.toggle("Activer", bot["actif"], key=f"actif_{id_bot}")
    bot["p_achat"] = st.number_input("Prix Achat", value=bot["p_achat"], format="%.4f", key=f"p_achat_{id_bot}")
    bot["p_vente"] = st.number_input("Prix Vente", value=bot["p_vente"], format="%.4f", key=f"p_vente_{id_bot}")
    bot["mise"] = st.number_input("Mise (USDC)", value=bot["mise"], format="%.4f", key=f"mise_{id_bot}")
   
    def start_bots():
        st.session_state.run = True
        st.session_state.stop_clicked = False
        if st.session_state.start_time is None:
            st.session_state.start_time = datetime.datetime.now()
            st.session_state.trade_count = 0
            st.session_state.start_capital = sum(b["mise"] for b in st.session_state.bots.values())

    def stop_bots():
        st.session_state.run = False
        st.session_state.stop_clicked = True

    # --- Bouton Sauvegarder ---
if st.button("💾 Sauvegarder", key=f"save_{id_bot}"):
    save_config(st.session_state.bots)
    st.toast(f"Bot {id_bot} sauvegardé ✔")
# --- Bouton Réinitialiser ---
if st.button("🗑 Réinitialiser le bot", key=f"reset_{id_bot}"):
    reset_bot(id_bot)

    if st.button("🗑 Réinitialiser le bot"):
        reset_bot(id_bot)
    st.divider()
    st.button("🚀 Démarrer", on_click=start_bots)
    st.button("🛑 Stop", on_click=stop_bots)

# ---- MÉTRIQUES RAPIDES ----
price = st.session_state.get("price")
usdc = st.session_state.get("usdc")
xrp = st.session_state.get("xrp")
gain_total = sum(b["gain_cumule"] for b in st.session_state.bots.values())
c1, c2, c3, c4 = st.columns(4)
c1.metric("Prix XRP", f"{price:.4f}" if price else "—")
c2.metric("USDC", f"{float(usdc):.4f}" if isinstance(usdc,(int,float)) else "0.0000")
c3.metric("XRP", f"{float(xrp):.4f}" if isinstance(xrp,(int,float)) else "0.0000")
c4.metric("Gain Total", f"{float(gain_total):.4f}" if isinstance(gain_total,(int,float)) else "0.0000")
st.divider()

# ---- TABLEAU DES BOTS ----
labels = ["N°", "État", "Achat", "Vente", "Mise", "Cycles", "Gain", "Action"]
cols = st.columns([0.4, 1.4, 1, 1, 1, 0.8, 1, 1])
for col, txt in zip(cols, labels):
    col.write(f"**{txt}**")

for i, bot in st.session_state.bots.items():
    if bot["actif"]:
        c = st.columns([0.4, 1.4, 1, 1, 1, 0.8, 1, 1])
        c[0].write(i)
        c[1].write(bot["etape"])
        c[2].write(bot["p_achat"])
        c[3].write(bot["p_vente"])
        c[4].write(round(bot["mise"], 4))
        c[5].write(bot["cycles"])
        c[6].write(round(bot["gain_cumule"], 4))
        order_id = bot.get("order_id")
        if order_id:
            if c[7].button("❌", key=f"cancel_{i}"):
                try:
                    exchange.cancel_order(order_id, symbol)
                    bot["order_id"] = None
                    bot["etape"] = "ATTENTE_VENTE" if bot["qty"] > 0 else "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"[Bot {i}] Ordre annulé manuellement")
                except Exception as e:
                    log(f"[Bot {i}] ERREUR annulation : {e}")
        else:
            c[7].write("—")

st.divider()

# ---- ORDRES LIMIT EN COURS ----
st.subheader("📋 Ordres LIMIT en cours")
cols = st.columns([0.4, 1.2, 1.2, 1])
cols[0].write("Bot")
cols[1].write("Étape")
cols[2].write("Order ID")
cols[3].write("Prix cible")
for i, bot in st.session_state.bots.items():
    oid = bot.get("order_id")
    if oid:
        c = st.columns([0.4, 1.2, 1.2, 1])
        c[0].write(i)
        c[1].write(bot["etape"])
        c[2].write(oid)
        c[3].write(bot["p_achat"] if bot["etape"] == "ACHAT_EN_COURS" else bot["p_vente"])

st.divider()

# ---- JOURNAL DES TRADES ----
st.subheader("📘 Journal des trades exécutés")
for t in st.session_state.trades[-50:]:
    st.write(f"{t['time']} | Bot {t['bot']} | {t['type']} | qty ={t['qty']} | price ={t['price']} | gain ={t['gain']}")

st.divider()

# ---- LOGS EN DIRECT ----
st.subheader("📝 Logs en direct")
for line in st.session_state.logs[-80:]:
    st.write(line)
## 🟪 BLOC 3 / 3 – INTERFACE COMPLÈTE + CHRONO PERSISTANT

st.title("🚀 XRP Sniper Pro – Auto‑Correct + Boule de Neige + %")
# ---- EN‑TÊTE COMPACT ----
gain_total=sum(b["gain_cumule"] for b in st.session_state.bots.values())
if st.session_state.run and st.session_state.start_time:
    elapsed=datetime.datetime.now()-st.session_state.start_time
    h,re=divmod(int(elapsed.total_seconds()),3600); m,s=divmod(re,60)
    elapsed_txt=f"{h:02d}:{m:02d}:{s:02d}"
    perf_txt=""
    if st.session_state.start_capital and st.session_state.start_capital>0:
        perf=(gain_total/st.session_state.start_capital)*100
        perf_txt=f"({perf:+.2f} %)"
    st.markdown(
        f"### 🟢 **RUNNING {elapsed_txt}** | 💹 Trades : {st.session_state.trade_count} "
        f"| 💰 Gain : {gain_total:.4f} USDC {perf_txt}"
    )
else:
    st.markdown("### 🔴 **BOTS ARRÊTÉS** | Aucun trade actif")
# ---- SIDEBAR : contrôles ----
# ------------------------------------------------------------
# CONFIGURATION SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ CONFIG BOT")

    id_bot = st.selectbox("Bot n°", range(1, 51), key="bot_select_sidebar")
    bot = st.session_state.bots[id_bot]

    bot["actif"] = st.toggle("Activer", bot["actif"], key=f"actif_{id_bot}")
    bot["p_achat"] = st.number_input("Prix Achat", value=bot["p_achat"], format="%.4f", key=f"p_achat_{id_bot}")
    bot["p_vente"] = st.number_input("Prix Vente", value=bot["p_vente"], format="%.4f", key=f"p_vente_{id_bot}")
    bot["mise"] = st.number_input("Mise (USDC)", value=bot["mise"], format="%.4f", key=f"mise_{id_bot}")

    # --- Bouton Sauvegarder ---
    if st.button("💾 Sauvegarder", key=f"save_{id_bot}"):
        save_config(st.session_state.bots)
        st.toast(f"Bot {id_bot} sauvegardé ✔")

    # --- Bouton Réinitialiser ---
    if st.button("🗑 Réinitialiser le bot", key=f"reset_{id_bot}"):
        reset_bot(id_bot)

    st.divider()

    # --- Boutons Démarrer / Stop ---
    def start_bots():
        st.session_state.run = True
        st.session_state.stop_clicked = False
        if st.session_state.start_time is None:
            st.session_state.start_time = datetime.datetime.now()
            st.session_state.trade_count = 0
            st.session_state.start_capital = sum(b["mise"] for b in st.session_state.bots.values())

    def stop_bots():
        st.session_state.run = False
        st.session_state.stop_clicked = True

    st.button("🚀 Démarrer", on_click=start_bots, key=f"start_{id_bot}")
    st.button("🛑 Stop", on_click=stop_bots, key=f"stop_{id_bot}")

# ---- MÉTRIQUES RAPIDES ----
price=st.session_state.get("price"); usdc=st.session_state.get("usdc"); xrp=st.session_state.get("xrp")
gain_total=sum(b["gain_cumule"] for b in st.session_state.bots.values())
c1,c2,c3,c4=st.columns(4)
c1.metric("Prix XRP",f"{price:.4f}" if price else "…")
c2.metric("USDC",f"{usdc:.4f}")
c3.metric("XRP",f"{xrp:.4f}")
c4.metric("Gain Total",f"{gain_total:.4f}")
st.divider()
# ---- TABLEAU DES BOTS ----
labels=["N°","État","Achat","Vente","Mise","Cycles","Gain","Action"]
cols=st.columns([0.4,1.4,1,1,1,0.8,1,1])
for col,txt in zip(cols,labels): col.write(f"**{txt}**")
for i,bot in st.session_state.bots.items():
    if bot["actif"]:
        c=st.columns([0.4,1.4,1,1,1,0.8,1,1])
        c[0].write(i); c[1].write(bot["etape"]); c[2].write(bot["p_achat"]); c[3].write(bot["p_vente"])
        c[4].write(round(bot["mise"],4)); c[5].write(bot["cycles"]); c[6].write(round(bot["gain_cumule"],4))
        order_id=bot.get("order_id")
        if order_id:
            if c[7].button("❌",key=f"cancel_{i}"):
                try:
                    exchange.cancel_order(order_id,symbol)
                    bot["order_id"]=None
                    bot["etape"]="ATTENTE_VENTE" if bot["qty"]>0 else "ATTENTE_ACHAT"
                    save_config(st.session_state.bots)
                    log(f"[Bot {i}] Ordre annulé manuellement")
                except Exception as e: log(f"[Bot {i}] ERREUR annulation : {e}")
        else: c[7].write("—")
st.divider()
# ---- ORDRES LIMIT EN COURS ----
st.subheader("📋 Ordres LIMIT en cours")
cols=st.columns([0.4,1.2,1.2,1])
cols[0].write("Bot"); cols[1].write("Étape"); cols[2].write("Order ID"); cols[3].write("Prix cible")
for i,bot in st.session_state.bots.items():
    oid=bot.get("order_id")
    if oid:
        c=st.columns([0.4,1.2,1.2,1]); c[0].write(i); c[1].write(bot["etape"]); c[2].write(oid)
        c[3].write(bot["p_achat"] if bot["etape"]=="ACHAT_EN_COURS" else bot["p_vente"])
st.divider()
# ---- JOURNAL DES TRADES ----
st.subheader("📘 Journal des trades exécutés")
for t in st.session_state.trades[-50:]:
    st.write(f"{t['time']} | Bot {t['bot']} | {t['type']} | qty = {t['qty']} | price = {t['price']} | gain = {t['gain']}")
st.divider()
# ---- LOGS EN DIRECT ----
st.subheader("📝 Logs en direct")
for line in st.session_state.logs[-80:]:
    st.write(line)










