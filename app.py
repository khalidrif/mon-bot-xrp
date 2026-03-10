import streamlit as st
import ccxt
import json
import os
import time

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="XRP Sniper Pro", layout="wide")
DB_FILE = "config_bots_xrp_secure.json"
symbol = "XRP/USDC"

if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# ------------------------------------------------------------
# AUTO-REFRESH
# ------------------------------------------------------------
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

if "run" not in st.session_state:
    st.session_state.run = False

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
        st.error("🔥 Tentative d'écraser avec fichier vide BLOQUÉE !")
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

st.title("✅ Bloc 1 chargé – Config OK")
st.write("Passe à la suite : Bloc 2 / 3 (logique du bot)")
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

    # ------------------------------------------------------------------
    # BOUCLE SUR LES 50 BOTS
    # ------------------------------------------------------------------
    for i, bot in st.session_state.bots.items():
        if not bot["actif"]:
            continue

        log(f"[Bot {i}] État={bot['etape']} Achat={bot['p_achat']} Vente={bot['p_vente']}")

        # ============ AUTO‑CORRECT : annule si prix modifié ==============
        order_id = bot.get("order_id")
        if order_id:
            try:
                order = exchange.fetch_order(order_id, symbol)
                if bot["etape"] == "ACHAT_EN_COURS" and float(order["price"]) != float(bot["p_achat"]):
                    exchange.cancel_order(order_id, symbol)
                    bot["order_id"] = None
                    bot["etape"] = "ATTENTE_ACHAT"
                    log(f"[Bot {i}] Auto‑correct BUY → ordre annulé")
                    save_config(st.session_state.bots)
                    continue
                if bot["etape"] == "VENTE_EN_COURS" and float(order["price"]) != float(bot["p_vente"]):
                    exchange.cancel_order(order_id, symbol)
                    bot["order_id"] = None
                    bot["etape"] = "ATTENTE_VENTE"
                    log(f"[Bot {i}] Auto‑correct SELL → ordre annulé")
                    save_config(st.session_state.bots)
                    continue
            except Exception as e:
                log(f"[Bot {i}] AUTO‑CORRECT erreur : {e}")

        # ===================== LIMIT BUY =====================
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

        # =================== SUIVI ACHAT =====================
        if bot["etape"] == "ACHAT_EN_COURS":
            try:
                order_id = bot.get("order_id")
                if not order_id:
                    continue
                order = exchange.fetch_order(order_id, symbol)
                if order["status"] == "closed":
                    bot["qty"] = float(order["filled"])
                    bot["etape"] = "ATTENTE_VENTE"
                    log(f"[Bot {i}] ACHAT executé qty={bot['qty']}")
                    st.session_state.trades.append({
                        "time": time.strftime("%H:%M:%S"),
                        "bot": i,
                        "type": "BUY",
                        "qty": bot["qty"],
                        "price": bot["p_achat"],
                        "gain": ""
                    })
                    st.session_state.trade_count += 1
                    save_trades_json(); save_trades_csv(); play_sound(); save_config(st.session_state.bots)
            except Exception as e:
                log(f"[Bot {i}] ERREUR ACHAT : {e}")

        # ===================== LIMIT SELL ====================
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

        # =================== SUIVI VENTE =====================
        if bot["etape"] == "VENTE_EN_COURS":
            try:
                order_id = bot.get("order_id")
                if not order_id:
                    continue
                order = exchange.fetch_order(order_id, symbol)
                if order["status"] == "closed":
                    gain = (bot["p_vente"] - bot["p_achat"]) * bot["qty"]
                    bot["cycles"] += 1
                    bot["gain_cumule"] += gain
                    bot["mise"] += gain    # effet boule de neige
                    bot["qty"] = 0
                    bot["etape"] = "ATTENTE_ACHAT"
                    log(f"[Bot {i}] VENTE executée gain = {gain} | nouvelle mise = {bot['mise']}")
                    st.session_state.trades.append({
                        "time": time.strftime("%H:%M:%S"),
                        "bot": i,
                        "type": "SELL",
                        "qty": "",
                        "price": bot["p_vente"],
                        "gain": round(gain, 6)
                    })
                    st.session_state.trade_count += 1
                    save_trades_json(); save_trades_csv(); play_sound(); save_config(st.session_state.bots)
            except Exception as e:
                log(f"[Bot {i}] ERREUR VENTE : {e}")

# Lance un cycle à chaque refresh
run_cycle()

st.write("✅ Bloc 2 chargé – logique du bot OK")


