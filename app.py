import streamlit as st
import time
import krakenex
import threading
import pandas as pd

running = False
profit_net = 0.0

# -------------------------------------------------------
# CONFIG KRAKEN API
# -------------------------------------------------------
api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

# -------------------------------------------------------
# PAIRE DÉTECTÉE (fixée : XRPRLUSD)
# -------------------------------------------------------
PAIR = "XRPRLUSD"
st.warning("Paire Kraken utilisée : " + PAIR)

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

def place_order(order_type, volume):
    if volume < 5:
        st.error(f"Volume insuffisant : {volume:.4f} XRP (minimum 5 XRP)")
        return {"error": ["volume too_small"], "result": {}}

    res = api.query_private("AddOrder", {
        "pair": PAIR,
        "type": order_type,
        "ordertype": "market",
        "volume": volume
    })

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

    df = pd.DataFrame(rows)
    df = df.sort_values("Heure", ascending=False)
    return df.head(25)

# -------------------------------------------------------
# THREAD BOT
# -------------------------------------------------------
def bot_thread(prix_achat, prix_vente, montant_usdc_initial, log, profit_box, history_box, snowball):
    global running, profit_net
    running = True

    position = 0
    prix_achat_reel = 0
    montant_usdc = montant_usdc_initial

    while running:
        prix = get_price()
        montant_xrp = montant_usdc / prix

        profit_box.info(f"Profit net : {profit_net:.4f} USDC")

        texte = (
            f"Prix XRP : {prix}\n"
            f"Trade : {montant_usdc:.4f} USDC → {montant_xrp:.4f} XRP\n"
            f"Profit net : {profit_net:.4f} USDC\n"
        )

        solde = get_usdc_balance()
        if position == 0 and solde < montant_usdc:
            st.warning(f"Solde insuffisant : {solde} USDC")
            time.sleep(3)
            continue

        if position == 0 and prix <= prix_achat:
            texte += f">>> ACHAT {montant_xrp:.4f} XRP à {prix}\n"
            prix_achat_reel = prix
            place_order("buy", montant_xrp)
            position = 1

        elif position == 1 and prix >= prix_vente:
            texte += f">>> VENTE {montant_xrp:.4f} XRP à {prix}\n"

            gain = (prix - prix_achat_reel) * (montant_usdc_initial / prix_achat_reel)
            profit_net += gain

            place_order("sell", montant_xrp)

            texte += f"Profit trade : {gain:.4f} USDC\n"
            texte += f"Profit total : {profit_net:.4f} USDC\n"

            position = 0

            if snowball:
                montant_usdc += gain
                texte += f"BOULE DE NEIGE : {montant_usdc:.4f} USDC\n"

        log.text(texte)

        try:
            df = get_order_history()
            history_box.dataframe(df)
        except:
            pass

        time.sleep(3)

# -------------------------------------------------------
# INTERFACE
# -------------------------------------------------------
st.title("BOT XRP/USDC – XRPRLUSD | Profit | Boule de Neige | Historique")

solde = get_usdc_balance()
st.info(f"Solde USDC actuel : {solde} USDC")

profit_box = st.info("Profit net : 0 USDC")
history_box = st.empty()
log = st.empty()

prix_achat = st.number_input("Prix d'achat (USDC)", min_value=0.0)
prix_vente = st.number_input("Prix de vente (USDC)", min_value=0.0)
montant_usdc = st.number_input("Montant USDC par trade", min_value=5.0)

snowball = st.checkbox("Activer Boule de Neige (réinvestit automatiquement)")

col1, col2 = st.columns(2)
with col1:
    start = st.button("Démarrer le bot")
with col2:
    stop = st.button("STOP BOT")

if start and not running:
    t = threading.Thread(target=bot_thread, args=(
        prix_achat, prix_vente, montant_usdc, log, profit_box, history_box, snowball
    ))
    t.start()
    st.success("Bot lancé !")

if stop:
    running = False
    st.error(f"Bot arrêté – Profit final : {profit_net:.4f} USDC")
