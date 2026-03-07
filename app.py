import streamlit as st
import time
import krakenex
import threading
import pandas as pd

running = False
profit_net = 0.0

api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XRPUSDC"   # confirmé par ton test

# --- helpers ---
def get_price():
    data = api.query_public("Ticker", {"pair": PAIR})
    return float(data["result"][PAIR]["c"][0])

def round_price(p):
    return float(f"{p:.5f}")

def get_usdc_balance():
    bal = api.query_private("Balance")
    if "result" in bal and "USDC" in bal["result"]:
        return float(bal["result"]["USDC"])
    return 0.0

def place_limit(order_type, price, volume):
    price = round_price(price)
    if volume < 5:
        st.error("Min 5 XRP")
        return {}

    order = {
        "pair": PAIR,
        "type": order_type,
        "ordertype": "limit",
        "price": price,
        "volume": volume,
        "oflags": "post"
    }

    res = api.query_private("AddOrder", order)
    if res["error"]:
        st.error("Erreur Kraken : " + str(res["error"]))
    return res

def get_history():
    res = api.query_private("TradesHistory")
    if "result" not in res:
        return pd.DataFrame()
    rows = []
    for tid, t in res["result"]["trades"].items():
        if t["pair"] == PAIR:
            rows.append({
                "Type": t["type"],
                "Prix": t["price"],
                "Vol XRP": t["vol"],
                "Coût USDC": t["cost"],
                "Heure": t["time"]
            })
    return pd.DataFrame(rows)

# ------------------ BOT LOGIC ------------------
def bot(prix_buy, prix_sell, montant_usdc, log, profit_box, hist_box):
    global running, profit_net
    running = True
    ordre = None
    position = 0
    prix_achat_reel = 0

    while running:
        prix = get_price()
        montant_xrp = montant_usdc / prix
        profit_box.info(f"Profit net : {profit_net:.4f} USDC")

        texte = f"Prix XRP : {prix}\nMontant : {montant_usdc} USDC → {montant_xrp:.4f} XRP\n"

        # LIMIT BUY visible
        if position == 0 and prix <= prix_buy and ordre is None:
            r = place_limit("buy", prix_buy, montant_xrp)
            if "txid" in r.get("result", {}):
                ordre = r["result"]["txid"][0]
                prix_achat_reel = prix_buy
                texte += f"LIMIT BUY créé : {ordre}\n"
                position = 1

        # LIMIT SELL visible
        if position == 1 and prix >= prix_sell and ordre is None:
            r = place_limit("sell", prix_sell, montant_xrp)
            if "txid" in r.get("result", {}):
                ordre = r["result"]["txid"][0]
                texte += f"LIMIT SELL créé : {ordre}\n"

        # vérifier exécution
        if ordre:
            q = api.query_private("QueryOrders", {"txid": ordre})
            info = q["result"][ordre]
            if info["status"] == "closed":
                texte += "Ordre exécuté\n"
                if position == 1:  # sell
                    gain = (prix_sell - prix_achat_reel) * (montant_usdc / prix_achat_reel)
                    profit_net += gain
                    texte += f"Profit : {gain:.4f} USDC\n"
                ordre = None
                position = 0

        log.text(texte)
        try:
            hist_box.dataframe(get_history())
        except:
            pass

        time.sleep(3)

# ------------------ UI ------------------
st.title("BOT XRP/USDC – LIMIT ORDERS (visible dans Kraken Orders)")

prix_actuel = get_price()
st.info(f"💰 Prix actuel XRP/USDC : {prix_actuel}")

profit_box = st.info("Profit net : 0 USDC")
history_box = st.empty()
log = st.empty()

prix_buy = st.number_input("Prix LIMIT BUY (≤ prix actuel)", min_value=0.0, format="%.5f")
prix_sell = st.number_input("Prix LIMIT SELL (≥ prix actuel)", min_value=0.0, format="%.5f")
montant_usdc = st.number_input("Montant USDC (5 XRP min)", min_value=5.0)

col1, col2 = st.columns(2)
with col1:
    start = st.button("Démarrer le bot")
with col2:
    stop = st.button("Stop bot")

if start:
    threading.Thread(target=bot, args=(prix_buy, prix_sell, montant_usdc, log, profit_box, history_box)).start()
    st.success("Bot lancé. Vérifie Kraken > Spot Orders")

if stop:
    running = False
    st.error("Bot arrêté.")
