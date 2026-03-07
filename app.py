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

PAIR = "XRPUSDC"
st.success("Paire Kraken : XRPUSDC (Limit Orders visibles dans Spot Orders)")

# Prix LIMIT autorisé par Kraken = max 5 décimales
def round_price(p):
    return float(f"{p:.5f}")

# -------------------------------------------------------
# KRAKEN HELPERS
# -------------------------------------------------------
def get_price():
    data = api.query_public("Ticker", {"pair": PAIR})
    return float(data["result"][PAIR]["c"][0])

def get_usdc_balance():
    bal = api.query_private("Balance")
    if "result" in bal and "USDC" in bal["result"]:
        return float(bal["result"]["USDC"])
    return 0.0

# LIMIT ORDER (VISIBLE DANS KRANKEN)
def place_order(order_type, price, volume):
    price = round_price(price)  # <= correction des 5 décimales

    if volume < 5:
        st.error(f"Volume trop faible : {volume:.4f} XRP (min = 5 XRP)")
        return {"error": ["EOrder:volume_too_small"], "result": {}}

    order = {
        "pair": PAIR,
        "type": order_type,
        "ordertype": "limit",
        "price": price,
        "volume": volume,
        "oflags": "post"  # L'ordre reste ouvert, visible dans 'Orders'
    }

    res = api.query_private("AddOrder", order)

    if "error" in res and len(res["error"]) > 0:
        st.error("Erreur Kraken : " + str(res["error"]))

    return res

def get_order_history():
    res = api.query_private("TradesHistory")
    if "result" not in res:
        return pd.DataFrame()
    rows = []
    for tid, t in res["result"]["trades"].items():
        if t["pair"] != PAIR:
            continue
        rows.append({
            "Type": t["type"].upper(),
            "Prix": float(t["price"]),
            "Volume XRP": float(t["vol"]),
            "Coût USDC": float(t["cost"]),
            "Heure": t["time"]
        })
    df = pd.DataFrame(rows).sort_values("Heure", ascending=False)
    return df.head(25)

# -------------------------------------------------------
# THREAD DU BOT
# -------------------------------------------------------
def bot_thread(prix_achat, prix_vente, montant_usdc_initial, log, profit_box, history_box, snowball):
    global running, profit_net

    running = True
    position = 0
    montant_usdc = montant_usdc_initial
    ordre_en_attente = None
    prix_achat_reel = 0

    while running:
        prix = get_price()
        montant_xrp = montant_usdc / prix

        profit_box.info(f"Profit net : {profit_net:.4f} USDC")

        texte = (
            f"Prix XRP : {prix}\n"
            f"Trade : {montant_usdc:.4f} USDC → {montant_xrp:.4f} XRP\n"
            f"Profit net : {profit_net:.4f} USDC\n"
        )

        # Vérification solde USDC
        if position == 0:
            solde = get_usdc_balance()
            if solde < montant_usdc:
                st.warning(f"Solde insuffisant : {solde} USDC")
                time.sleep(3)
                continue

        # ---------- LIMIT BUY ----------
        if position == 0 and prix <= prix_achat and ordre_en_attente is None:
            prix_achat_limit = round_price(prix_achat)
            texte += f">>> LIMIT BUY {montant_xrp:.4f} XRP @ {prix_achat_limit}\n"

            res = place_order("buy", prix_achat_limit, montant_xrp)
            if "result" in res and "txid" in res["result"]:
                ordre_en_attente = res["result"]["txid"][0]
                texte += "Ordre BUY visible dans Kraken : " + ordre_en_attente + "\n"
                prix_achat_reel = prix_achat_limit
            position = 1

        # ---------- LIMIT SELL ----------
        elif position == 1 and prix >= prix_vente and ordre_en_attente is None:
            prix_vente_limit = round_price(prix_vente)
            texte += f">>> LIMIT SELL {montant_xrp:.4f} XRP @ {prix_vente_limit}\n"

            res = place_order("sell", prix_vente_limit, montant_xrp)
            if "result" in res and "txid" in res["result"]:
                ordre_en_attente = res["result"]["txid"][0]
                texte += "Ordre SELL visible dans Kraken : " + ordre_en_attente + "\n"

        # ---------- Vérifier si ordres exécutés ----------
        if ordre_en_attente:
            check = api.query_private("QueryOrders", {"txid": ordre_en_attente})
            if "result" in check and ordre_en_attente in check["result"]:
                info = check["result"][ordre_en_attente]

                if info["status"] == "closed":
                    texte += "Ordre exécuté : " + ordre_en_attente + "\n"

                    # Si SELL exécuté => profit
                    if position == 1:
                        gain = (prix_vente - prix_achat_reel) * (montant_usdc_initial / prix_achat_reel)
                        profit_net += gain
                        texte += f"Profit trade : {gain:.4f} USDC\n"

                        if snowball:
                            montant_usdc += gain
                            texte += f"BOULE DE NEIGE → {montant_usdc:.4f} USDC\n"

                    ordre_en_attente = None
                    position = 0

        log.text(texte)

        # Historique
        try:
            history_box.dataframe(get_order_history())
        except:
            pass

        time.sleep(3)

# -------------------------------------------------------
# INTERFACE
# -------------------------------------------------------
st.title("BOT XRP/USDC – LIMIT ORDERS (VISIBLE DANS SPOT ORDERS)")

solde = get_usdc_balance()
st.info(f"Solde USDC : {solde} USDC")

profit_box = st.info("Profit net : 0 USDC")
history_box = st.empty()
log = st.empty()

prix_achat = st.number_input("Prix LIMIT BUY (max 5 décimales)", min_value=0.0, format="%.5f")
prix_vente = st.number_input("Prix LIMIT SELL (max 5 décimales)", min_value=0.0, format="%.5f")
montant_usdc = st.number_input("Montant USDC par trade (min 5 XRP)", min_value=5.0)

snowball = st.checkbox("Activer Boule de Neige")

col1, col2 = st.columns(2)
with col1:
    start = st.button("Démarrer le bot")
with col2:
    stop = st.button("STOP BOT")

if start and not running:
    t = threading.Thread(
        target=bot_thread,
        args=(prix_achat, prix_vente, montant_usdc, log, profit_box, history_box, snowball)
    )
    t.start()
    st.success("Bot lancé ! Vos LIMIT orders seront visibles dans Kraken.")

if stop:
    running = False
    st.error(f"Bot arrêté – Profit final : {profit_net:.4f} USDC")
