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
# ------------------------------------------------------------
# SON "ding" pour les trades
# ------------------------------------------------------------
def play_sound():
    st.markdown("""
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg">
        </audio>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------
# FONCTION PRINCIPALE : RUN CYCLE
# ------------------------------------------------------------
def run_cycle():

    # ----- 1. Lecture du ticker -----
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
        log(f"Prix reçu : {price}")
    except Exception as e:
        price = None
        log(f"[ERREUR TICKER] {e}")

    # ----- 2. Lecture du solde -----
    try:
        bal = exchange.fetch_balance()
        usdc = bal["free"].get("USDC", 0)
        xrp  = bal["free"].get("XRP", 0)
        log(f"USDC={usdc} | XRP={xrp}")
    except Exception as e:
        usdc = 0
        xrp = 0
        log(f"[ERREUR BALANCE] {e}")

    st.session_state.price = price
    st.session_state.usdc = usdc
    st.session_state.xrp = xrp

    # ----- 3. Si bots arrêtés -----
    if not st.session_state.run:
        log("Bots arrêtés")
        return

    # ----- 4. Boucle sur tous les bots -----
    for i, bot in st.session_state.bots.items():

        if not bot["actif"]:
            continue

        log(f"[Bot {i}] État={bot['etape']} Achat={bot['p_achat']} Vente={bot['p_vente']}")

        # ===== AUTO-CORRECT : Annule l'ordre si le prix ciblé a changé =====
        order_id = bot.get("order_id")
        if order_id:
            try:
                order = exchange.fetch_order(order_id, symbol)
                if bot["etape"] == "ACHAT_EN_COURS" and float(order["price"]) != float(bot["p_achat"]):
                    exchange.cancel_order(order_id, symbol)
                    bot["order_id"] = None
                    bot["etape"] = "ATTENTE_ACHAT"
                    log(f"[Bot {i}] Auto-correct BUY annulé")
                    save_config(st.session_state.bots)
                    continue

                if bot["etape"] == "VENTE_EN_COURS" and float(order["price"]) != float(bot["p_vente"]):
                    exchange.cancel_order(order_id, symbol)
                    bot["order_id"] = None
                    bot["etape"] = "ATTENTE_VENTE"
                    log(f"[Bot {i}] Auto-correct SELL annulé")
                    save_config(st.session_state.bots)
                    continue

            except Exception as e:
                log(f"[Bot {i}] ERREUR AUTO-CORRECT : {e}")

        # ===== ACHAT LIMIT =====
        if bot["etape"] == "ATTENTE_ACHAT" and price and price <= bot["p_achat"] and usdc >= bot["mise"]:
            try:
                mise_net = bot["mise"] * 0.985
                qty = float(exchange.amount_to_precision(symbol, mise_net / price))
                order = exchange.create_limit_buy_order(symbol, qty, bot["p_achat"])
                bot["order_id"] = order["id"]
                bot["etape"] = "ACHAT_EN_COURS"
                log(f"[Bot {i}] LIMIT BUY placé à {bot['p_achat']} qty={qty}")
                save_config(st.session_state.bots)

            except Exception as e:
                log(f"[Bot {i}] ERREUR LIMIT BUY : {e}")

        # ===== SUIVI D'ACHAT =====
        if bot["etape"] == "ACHAT_EN_COURS":
            try:
                oid = bot.get("order_id")
                if not oid:
                    continue
                order = exchange.fetch_order(oid, symbol)

                if order["status"] == "closed":
                    bot["qty"] = float(order["filled"])
                    bot["etape"] = "ATTENTE_VENTE"
                    log(f"[Bot {i}] ACHAT exécuté qty={bot['qty']}")

                    # Journal de trade
                    st.session_state.trades.append({
                        "time": time.strftime("%H:%M:%S"),
                        "bot": i,
                        "type": "BUY",
                        "qty": bot["qty"],
                        "price": bot["p_achat"],
                        "gain": ""
                    })
                    st.session_state.trade_count += 1

                    save_trades_json()
                    save_trades_csv()
                    play_sound()
                    save_config(st.session_state.bots)

            except Exception as e:
                log(f"[Bot {i}] ERREUR SUIVI ACHAT : {e}")

        # ===== VENTE LIMIT =====
        if bot["etape"] == "ATTENTE_VENTE" and bot["qty"] > 0 and price and price >= bot["p_vente"]:
            try:
                qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.99))
                order = exchange.create_limit_sell_order(symbol, qty_sell, bot["p_vente"])
                bot["order_id"] = order["id"]
                bot["etape"] = "VENTE_EN_COURS"
                log(f"[Bot {i}] LIMIT SELL placé à {bot['p_vente']} qty={qty_sell}")
                save_config(st.session_state.bots)

            except Exception as e:
                log(f"[Bot {i}] ERREUR LIMIT SELL : {e}")

        # ===== SUIVI DE VENTE =====
        if bot["etape"] == "VENTE_EN_COURS":
            try:
                oid = bot.get("order_id")
                if not oid:
                    continue
                order = exchange.fetch_order(oid, symbol)

                if order["status"] == "closed":
                    gain = (bot["p_vente"] - bot["p_achat"]) * bot["qty"]

                    bot["cycles"] += 1
                    bot["gain_cumule"] += gain
                    bot["mise"] += gain   # effet boule de neige

                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"

                    log(f"[Bot {i}] VENTE exécutée gain={gain} | nouvelle mise={bot['mise']}")

                    # Journal de trade
                    st.session_state.trades.append({
                        "time": time.strftime("%H:%M:%S"),
                        "bot": i,
                        "type": "SELL",
                        "qty": "",
                        "price": bot["p_vente"],
                        "gain": round(gain, 6)
                    })
                    st.session_state.trade_count += 1

                    save_trades_json()
                    save_trades_csv()
                    play_sound()
                    save_config(st.session_state.bots)

            except Exception as e:
                log(f"[Bot {i}] ERREUR SUIVI VENTE : {e}")

    # Fin de la boucle des bots


# Lance un cycle à chaque refresh
run_cycle()

st.write("✅ Bloc 2 chargé – logique du bot OK")

## 🟪 BLOC 3 / 3 – INTERFACE COMPLÈTE + CHRONO PERSISTANT
```python
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
with st.sidebar:
    st.header("⚙️ CONFIG BOT")
    id_bot=st.selectbox("Bot n°",range(1,51))
    bot=st.session_state.bots[id_bot]
    bot["actif"]=st.toggle("Activer",bot["actif"])
    bot["p_achat"]=st.number_input("Prix Achat",value=bot["p_achat"],format="%.4f")
    bot["p_vente"]=st.number_input("Prix Vente",value=bot["p_vente"],format="%.4f")
    bot["mise"]=st.number_input("Mise (USDC)",value=bot["mise"],format="%.4f")

    def start_bots():
        st.session_state.run=True; st.session_state.stop_clicked=False
        if st.session_state.start_time is None:
            st.session_state.start_time=datetime.datetime.now()
            st.session_state.trade_count=0
            st.session_state.start_capital=sum(b["mise"] for b in st.session_state.bots.values())

    def stop_bots():
        st.session_state.run=False; st.session_state.stop_clicked=True

    if st.button("💾 Sauvegarder"): save_config(st.session_state.bots); st.toast("Sauvegardé ✔")
    if st.button("🗑 Réinitialiser le bot"): reset_bot(id_bot)
    st.divider()
    st.button("🚀 Démarrer",on_click=start_bots)
    st.button("🛑 Stop",on_click=stop_bots)

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

