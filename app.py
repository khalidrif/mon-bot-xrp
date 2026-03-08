import streamlit as st
import ccxt
import json, os, time

st.set_page_config(page_title="Bots Snowball XRP/USDC", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"


# ---------------------------
# SAVE / LOAD
# ---------------------------
def load_bots():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return []


def save_bots():
    with open(SAVE_FILE, "w") as f:
        json.dump(st.session_state.bots, f, indent=4)


# ---------------------------
# INIT SESSION
# ---------------------------
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

if "last_run" not in st.session_state:
    st.session_state.last_run = 0


# ---------------------------
# CONNECT KRAKEN
# ---------------------------
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True
    })
except:
    st.error("Erreur API Kraken")
    st.stop()


# ---------------------------
# GET PRICE
# ---------------------------
def get_price():
    try:
        return exchange.fetch_ticker("XRP/USDC")["last"]
    except:
        return None


prix = get_price()

st.title("❄️ Snowball XRP/USDC – BUY MARKET + SELL LIMIT")

if prix:
    st.metric("Prix XRP/USDC", f"{prix:.4f}")
else:
    st.stop()


# ---------------------------
# Solde
# ---------------------------
bal = exchange.fetch_balance()
usdc = bal["free"].get("USDC", 0.0)
xrp = bal["free"].get("XRP", 0.0)

st.metric("USDC Disponible", f"{usdc:.4f}")
st.metric("XRP Disponible", f"{xrp:.4f}")


# ---------------------------
# AJOUT BOT
# ---------------------------
if st.button("➕ Ajouter un bot"):
    st.session_state.bots.append({
        "enabled": False,
        "mode": "OFF",   # OFF⚫ , BUY🟢 , SELL🔴
        "usdc": 15.0,
        "buy": prix * 0.99,     # déclenchement d'achat
        "sell": prix * 1.01,    # prix LIMIT de vente
        "entry": None,
        "xrp_qty": 0.0,
        "gain": 0.0,
        "cycles": 0
    })
    save_bots()
    st.rerun()


# ---------------------------
# AFFICHAGE
# ---------------------------
for i, bot in enumerate(st.session_state.bots):

    col0, colU, col1, col2, col3, col4, col5, col6 = st.columns([1,2,3,3,3,3,2,1])

    # Pastille
    col0.write("⚫" if bot["mode"] == "OFF" else ("🟢" if bot["mode"] == "BUY" else "🔴"))

    # USDC montant
    bot["usdc"] = colU.number_input(
        "USDC",
        min_value=5.0,
        value=float(bot["usdc"]),
        step=1.0,
        key=f"u{i}"
    )

    # BUY TRIGGER CONDITION
    bot["buy"] = col1.number_input(
        "Achat si prix ≤",
        value=float(bot["buy"]),
        format="%.4f",
        key=f"b{i}"
    )

    # SELL LIMIT PRICE
    bot["sell"] = col2.number_input(
        "Sell LIMIT ≥",
        value=float(bot["sell"]),
        format="%.4f",
        key=f"s{i}"
    )

    # Gain + Cycles
    col3.metric("Gain", f"{bot['gain']:.4f}")
    col4.metric("Cycles", bot["cycles"])

    # Start / Stop
    if bot["enabled"]:
        if col5.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "OFF"
            save_bots()
            st.rerun()
    else:
        if col5.button("Start", key=f"start{i}"):
            bot["enabled"] = True
            bot["mode"] = "BUY"
            save_bots()
            st.rerun()

    # DELETE
    if col6.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()


# ---------------------------
# LOGIQUE TRADING
# ---------------------------
now = time.time()
if now - st.session_state.last_run > 2:
    st.session_state.last_run = now

    prix = get_price()
    if not prix:
        st.stop()

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        # ------------------------------------------------
        # MODE BUY → MARKET (NE PEUT PAS ÊTRE PARTIEL)
        # ------------------------------------------------
        if bot["mode"] == "BUY":

            if prix <= bot["buy"]:

                qty = round(bot["usdc"] / prix, 6)

                try:
                    order = exchange.create_market_buy_order("XRP/USDC", qty)
                except Exception as e:
                    st.error(f"Erreur BUY MARKET : {e}")
                    continue

                # XRP achetés réellement
                filled = order["filled"]
                if filled < 5:
                    st.warning(f"Achat insuffisant ({filled} XRP), skip")
                    continue

                bot["entry"] = prix
                bot["xrp_qty"] = filled
                bot["mode"] = "SELL"
                save_bots()

        # ------------------------------------------------
        # MODE SELL → LIMIT
        # ------------------------------------------------
        elif bot["mode"] == "SELL":

            try:
                order = exchange.create_limit_sell_order("XRP/USDC", bot["xrp_qty"], bot["sell"])
            except Exception as e:
                st.error(f"Erreur SELL LIMIT : {e}")
                continue

            # Si vendu
            try:
                o = exchange.fetch_order(order["id"], "XRP/USDC")
                if o["status"] == "closed":
                    gain = (bot["sell"] - bot["entry"]) * bot["xrp_qty"]
                    bot["gain"] += gain
                    bot["cycles"] += 1
                    bot["mode"] = "BUY"
                    bot["entry"] = None
                    save_bots()
            except:
                pass


save_bots()
