import streamlit as st
import ccxt
import json
import os
import time

st.set_page_config(page_title="XRP Sniper Pro", layout="wide")
DB_FILE = "config_bots_xrp_secure.json"
symbol = "XRP/USDC"

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

def auto_refresh():
    st.markdown("""
        <script>
            setTimeout(function() {
                document.getElementById('refresh_button').click();
            }, 800);   /* rafraîchit toutes les 0.8 s */
        </script>
    """, unsafe_allow_html=True)
    st.button("refresh", key="refresh_button")

auto_refresh()

if "run" not in st.session_state:
    st.session_state.run = False

# JOURNAL DES TRADES
if "trades" not in st.session_state:
    st.session_state.trades = []

def save_trades_json():
    with open("trades_log.json", "w") as f:
        json.dump(st.session_state.trades, f, indent=2)

def save_trades_csv():
    with open("trades_log.csv", "w") as f:
        f.write("time,bot,type,qty,price,gain\n")
        for t in st.session_state.trades:
            f.write(",".join(str(x) for x in t.values()) + "\n")

def save_config(bots):
    try:
        with open("backup_config.json", "w") as bkp:
            json.dump(bots, bkp)
    except:
        pass
    if not isinstance(bots, dict) or len(bots) == 0:
        st.error("🔥 Tentative d'écraser avec fichier vide BLOQUÉE !")
        return
    try:
        with open(DB_FILE, "w") as f:
            json.dump(bots, f)
    except Exception as e:
        st.error(f"❌ ERREUR SAUVEGARDE : {e}")

def load_config():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict) or len(data) == 0:
                raise ValueError("Config vide/corrompue")
            return {int(k): v for k, v in data.items()}
        except:
            st.warning("⚠️ Config corrompue → restauration backup…")
            if os.path.exists("backup_config.json"):
                with open("backup_config.json", "r") as f:
                    backup = json.load(f)
                st.success("✨ Backup restauré")
                return {int(k): v for k, v in backup.items()}
            else:
                st.error("❌ Aucun backup trouvé")
                return None
    return None

def reset_bot(i):
    st.session_state.bots[i] = {
        "actif": False,
        "p_achat": 1.35,
        "p_vente": 1.38,
        "mise": 15.0,
        "etape": "ATTENTE_ACHAT",
        "qty": 0.0,
        "cycles": 0,
        "gain_cumule": 0.0,
        "order_id": None
    }
    save_config(st.session_state.bots)
    log(f"Bot #{i} réinitialisé")

if "bots" not in st.session_state:
    cfg = load_config()
    if cfg:
        st.session_state.bots = cfg
    else:
        st.session_state.bots = {
            i: {
                "actif": False,
                "p_achat": 1.35,
                "p_vente": 1.38,
                "mise": 15.0,
                "etape": "ATTENTE_ACHAT",
                "qty": 0.0,
                "cycles": 0,
                "gain_cumule": 0.0,
                "order_id": None
            }
            for i in range(1, 51)
        }
        save_config(st.session_state.bots)

for bot in st.session_state.bots.values():
    if "order_id" not in bot:
        bot["order_id"] = None

@st.cache_resource
def get_exchange():
    ex = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True,
    })
    ex.load_markets()
    return ex

exchange = get_exchange()
def play_sound():
    st.markdown("""
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg">
        </audio>
    """, unsafe_allow_html=True)

def run_cycle():
    try:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker["last"]
        log(f"Prix reçu : {price}")
    except Exception as e:
        price = None
        log(f"[ERREUR TICKER] {e}")

    try:
        bal = exchange.fetch_balance()
        usdc = bal["free"].get("USDC", 0)
        xrp  = bal["free"].get("XRP", 0)
        log(f"USDC={usdc} | XRP={xrp}")
    except Exception as e:
        usdc = xrp = 0
        log(f"[ERREUR BALANCE] {e}")

    st.session_state.price = price
    st.session_state.usdc = usdc
    st.session_state.xrp = xrp

    if not st.session_state.run:
        log("Bots arrêtés")
        return

    for i, bot in st.session_state.bots.items():
        if not bot["actif"]:
            continue

        log(f"[Bot {i}] État={bot['etape']} Achat={bot['p_achat']} Vente={bot['p_vente']}")

        # AUTO‑CORRECT si prix changé
        order_id = bot.get("order_id")
        if order_id:
            try:
                order = exchange.fetch_order(order_id, symbol)
                if bot["etape"] == "ACHAT_EN_COURS" and float(order["price"]) != float(bot["p_achat"]):
                    exchange.cancel_order(order_id, symbol)
                    bot["order_id"] = None
                    bot["etape"] = "ATTENTE_ACHAT"
                    log(f"[Bot {i}] Auto‑correct BUY : ordre annulé")
                    save_config(st.session_state.bots)
                    continue
                if bot["etape"] == "VENTE_EN_COURS" and float(order["price"]) != float(bot["p_vente"]):
                    exchange.cancel_order(order_id, symbol)
                    bot["order_id"] = None
                    bot["etape"] = "ATTENTE_VENTE"
                    log(f"[Bot {i}] Auto‑correct SELL : ordre annulé")
                    save_config(st.session_state.bots)
                    continue
            except Exception as e:
                log(f"[Bot {i}] AUTO‑CORRECT erreur : {e}")

        # LIMIT BUY
        if bot["etape"] == "ATTENTE_ACHAT" and price and price <= bot["p_achat"] and usdc >= bot["mise"]:
            try:
                mise_net = bot["mise"] * 0.985
                qty = float(exchange.amount_to_precision(symbol, mise_net / price))
                order = exchange.create_limit_buy_order(symbol, qty, bot["p_achat"])
                bot["order_id"] = order["id"]
                bot["etape"] = "ACHAT_EN_COURS"
                log(f"[Bot {i}] LIMIT BUY placé {bot['p_achat']} qty={qty}")
                save_config(st.session_state.bots)
            except Exception as e:
                log(f"[Bot {i}] ERREUR BUY : {e}")

        # Suivi ACHAT
        if bot["etape"] == "ACHAT_EN_COURS":
            try:
                order_id = bot.get("order_id")
                if not order_id: continue
                order = exchange.fetch_order(order_id, symbol)
                if order["status"] == "closed":
                    bot["qty"] = float(order["filled"])
                    bot["etape"] = "ATTENTE_VENTE"
                    log(f"[Bot {i}] ACHAT executé qty={bot['qty']}")
                    st.session_state.trades.append({
                        "time": time.strftime("%H:%M:%S"),
                        "bot": i, "type": "BUY",
                        "qty": bot["qty"], "price": bot["p_achat"], "gain": ""
                    })
                    st.session_state.trade_count += 1
                    save_trades_json(); save_trades_csv(); play_sound(); save_config(st.session_state.bots)
            except Exception as e:
                log(f"[Bot {i}] ERREUR ACHAT : {e}")

        # LIMIT SELL
        if bot["etape"] == "ATTENTE_VENTE" and bot["qty"] > 0 and price and price >= bot["p_vente"]:
            try:
                qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.99))
                order = exchange.create_limit_sell_order(symbol, qty_sell, bot["p_vente"])
                bot["order_id"] = order["id"]
                bot["etape"] = "VENTE_EN_COURS"
                log(f"[Bot {i}] LIMIT SELL placé {bot['p_vente']} qty={qty_sell}")
                save_config(st.session_state.bots)
            except Exception as e:
                log(f"[Bot {i}] ERREUR SELL : {e}")

        # Suivi VENTE (BOULE DE NEIGE)
        if bot["etape"] == "VENTE_EN_COURS":
            try:
                order_id = bot.get("order_id")
                if not order_id: continue
                order = exchange.fetch_order(order_id, symbol)
                if order["status"] == "closed":
                    gain = (bot["p_vente"] - bot["p_achat"]) * bot["qty"]
                    bot["cycles"] += 1
                    bot["gain_cumule"] += gain
                    bot["mise"] += gain  # effet boule de neige
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    log(f"[Bot {i}] VENTE executée gain={gain} | nouvelle mise={bot['mise']}")
                    st.session_state.trades.append({
                        "time": time.strftime("%H:%M:%S"),
                        "bot": i, "type": "SELL",
                        "qty": "", "price": bot["p_vente"], "gain": round(gain, 6)
                    })
                    st.session_state.trade_count += 1
                    save_trades_json(); save_trades_csv(); play_sound(); save_config(st.session_state.bots)
            except Exception as e:
                log(f"[Bot {i}] ERREUR VENTE : {e}")

run_cycle()
st.title("🚀 XRP Sniper Pro – Auto‑Correct + Boule de Neige + %")

# EN‑TÊTE PRO
import datetime
if "start_time" not in st.session_state: st.session_state.start_time=None
if "trade_count" not in st.session_state: st.session_state.trade_count=0
if "start_capital" not in st.session_state: st.session_state.start_capital=None
current_capital = sum(b["mise"] for b in st.session_state.bots.values())
if st.session_state.run and st.session_state.start_time is None:
    st.session_state.start_time=datetime.datetime.now()
    st.session_state.trade_count=0
    st.session_state.start_capital=current_capital
if not st.session_state.run and st.session_state.start_time is not None:
    st.session_state.start_time=None
    st.session_state.start_capital=None
gain_total = sum(b["gain_cumule"] for b in st.session_state.bots.values())
elapsed_txt=""
if st.session_state.run and st.session_state.start_time:
    elapsed=datetime.datetime.now()-st.session_state.start_time
    h,rem=divmod(int(elapsed.total_seconds()),3600)
    m,s=divmod(rem,60)
    elapsed_txt=f"{h:02d}:{m:02d}:{s:02d}"
perf_txt=""
if st.session_state.start_capital and st.session_state.start_capital>0:
    perf=(gain_total/st.session_state.start_capital)*100
    sign="+" if perf>=0 else ""
    perf_txt=f"({sign}{perf:.2f} %)"
if st.session_state.run and st.session_state.start_time:
    st.markdown(
        f"### 🟢 **RUNNING {elapsed_txt}** | 💹 Trades : {st.session_state.trade_count} "
        f"| 💰 Gain : {gain_total:.4f} USDC {perf_txt}"
    )
else:
    st.markdown("### 🔴 **BOTS ARRÊTÉS** | Aucun trade actif")

# --- reste : config + tableaux + logs ---
# (tu gardes le même contenu d’UI : sidebar, métriques, tableau des bots, logs en direct)
