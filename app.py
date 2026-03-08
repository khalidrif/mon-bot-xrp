import streamlit as st
import ccxt
import json, os, time

st.set_page_config(page_title="Bots Snowball XRP/USDC", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

# ----------------------------------------------------
# SAVE / LOAD
# ----------------------------------------------------
def load_bots():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return []

def save_bots():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)

# ----------------------------------------------------
# INIT
# ----------------------------------------------------
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

if "last_run" not in st.session_state:
    st.session_state.last_run = 0

# ----------------------------------------------------
# CONNECT KRAKEN
# ----------------------------------------------------
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True
    })
except:
    st.error("Erreur API Kraken")
    st.stop()

# ----------------------------------------------------
# PRICE
# ----------------------------------------------------
def get_price():
    try:
        return exchange.fetch_ticker("XRP/USDC")["last"]
    except:
        return None

prix = get_price()
st.title("❄️ Snowball XRP/USDC – Version Stable & Finale")

if prix is None:
    st.error("Impossible d'obtenir le prix.")
    st.stop()

st.metric("Prix XRP/USDC", f"{prix:.4f}")

# ----------------------------------------------------
# BALANCES Kraken
# ----------------------------------------------------
try:
    bal = exchange.fetch_balance()
    usdc_kraken = bal["free"].get("USDC", 0.0)
except:
    usdc_kraken = 0.0

st.metric("USDC Kraken disponible", f"{usdc_kraken:.4f}")

# ----------------------------------------------------
# AJOUT BOT
# ----------------------------------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "OFF",    # OFF ⚫ | BUY 🟢 | SELL 🔴
        "usdc": 20.0,     # montant utilisé pour ACHAT
        "buy_trigger": prix * 0.99,
        "sell_price": prix * 1.01,
        "entry": None,
        "xrp_qty": 0.0,   # quantité achetée PAR CE BOT
        "gain": 0.0,
        "cycles": 0
    })
    save_bots()
    st.rerun()

# ----------------------------------------------------
# AFFICHAGE BOTS
# ----------------------------------------------------
for i, bot in enumerate(st.session_state.bots):
    
    col0, colU, col1, col2, col3, col4, col5, col6 = st.columns([1,2,3,3,3,3,2,1])

    # PASTILLE
    if bot["mode"] == "OFF":
        col0.write("⚫")
    elif bot["mode"] == "BUY":
        col0.write("🟢")
    else:
        col0.write("🔴")

    # USDC à utiliser
    bot["usdc"] = colU.number_input(
        "USDC",
        min_value=5.0,
        value=float(bot["usdc"]),
        key=f"usdc{i}"
    )

    # BUY condition
    bot["buy_trigger"] = col1.number_input(
        "Buy si prix ≤",
        value=float(bot["buy_trigger"]),
        format="%.4f",
        key=f"buy{i}"
    )

    # SELL limit price
    bot["sell_price"] = col2.number_input(
        "Sell LIMIT ≥",
        value=float(bot["sell_price"]),
        format="%.4f",
        key=f"sell{i}"
    )

    # Gain & cycles
    col3.metric("Gain", f"{bot['gain']:.4f}")
    col4.metric("Cycles", bot["cycles"])

    # START / STOP
    if bot["enabled"]:
        if col5.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "OFF"
            bot["entry"] = None
            save_bots()
            st.rerun()
    else:
        if col5.button("Start", key=f"start{i}"):
            bot["enabled"] = True
            bot["mode"] = "BUY"
            save_bots()
            st.rerun()

    # DELETE BOT
    if col6.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()

# ----------------------------------------------------
# LOGIQUE TRADING — ULTRA STABLE
# ----------------------------------------------------
now = time.time()
if now - st.session_state.last_run > 2:
    st.session_state.last_run = now

    prix = get_price()
    if prix is None:
        st.stop()

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        # ------------------------------------------------
        # MODE BUY → MARKET (jamais partiel)
        # ------------------------------------------------
        if bot["mode"] == "BUY":

            if prix <= bot["buy_trigger"]:

                qty = round(bot["usdc"] / prix, 6)
                if qty < 5:
                    continue  # trop petit pour XRPKraken (min ~5 XRP)

                try:
                    order = exchange.create_market_buy_order("XRP/USDC", qty)
                except Exception as e:
                    st.error(f"Erreur BUY MARKET : {e}")
                    continue

                filled_qty = order.get("filled", 0)

                # sécurité : minimum 5 XRP après frais
                if filled_qty < 5:
                    st.warning(f"Achat insuffisant ({filled_qty} XRP).")
                    continue

                # On enregistre EXACTEMENT la quantité achetée
                bot["xrp_qty"] = filled_qty
                bot["entry"] = prix
                bot["mode"] = "SELL"
                save_bots()

        # ------------------------------------------------
        # MODE SELL → LIMIT (quantité exacte du bot)
        # ------------------------------------------------
        elif bot["mode"] == "SELL":

            # Toujours vendre EXACTEMENT la quantité ACHETÉE par CE bot
            sell_qty = round(bot["xrp_qty"], 6)

            if sell_qty < 5:
                continue  # éviter erreur Kraken

            try:
                order = exchange.create_limit_sell_order("XRP/USDC", sell_qty, bot["sell_price"])
                order_id = order["id"]
            except Exception as e:
                st.error(f"Erreur SELL LIMIT : {e}")
                continue

            # Vérifier exécution
            try:
                o = exchange.fetch_order(order_id, "XRP/USDC")
                if o["status"] == "closed":

                    gain = (bot["sell_price"] - bot["entry"]) * sell_qty
                    bot["gain"] += gain
                    bot["cycles"] += 1

                    # RESET SNOWBALL
                    bot["entry"] = None
                    bot["xrp_qty"] = 0
                    bot["mode"] = "BUY"

                    save_bots()
            except:
                pass

save_bots()
