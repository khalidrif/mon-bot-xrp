import streamlit as st
import time
import krakenex
import threading

running = False
profit_net = 0.0

api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

def get_price():
    data = api.query_public("Ticker", {"pair": "XRPUSD"})
    return float(data["result"]["XXRPZUSD"]["c"][0])

def place_order(order_type, volume):
    return api.query_private("AddOrder", {
        "pair": "XRPUSD",
        "type": order_type,
        "ordertype": "market",
        "volume": volume
    })

def get_usdc_balance():
    balance = api.query_private("Balance")
    if "result" in balance and "USDC" in balance["result"]:
        return float(balance["result"]["USDC"])
    return 0.0

def bot_thread(prix_achat, prix_vente, montant_usdc_initial, log, profit_display, snowball):
    global running, profit_net
    running = True
    position = 0
    prix_achat_reel = 0
    montant_usdc = montant_usdc_initial

    while running:
        prix = get_price()
        montant_xrp = montant_usdc / prix

        texte = ""
        texte += "Prix XRP : " + str(prix) + "\n"
        texte += "Montant trade : " + str(montant_usdc) + " USDC → " + str(round(montant_xrp, 4)) + " XRP\n"
        texte += "Profit net actuel : " + str(round(profit_net, 4)) + " USDC\n"

        profit_display.info("Profit net : " + str(round(profit_net, 4)) + " USDC")

        if position == 0 and prix <= prix_achat:
            texte += "\n>>> ACHAT à " + str(prix) + "\n"
            prix_achat_reel = prix
            place_order("buy", montant_xrp)
            position = 1

        elif position == 1 and prix >= prix_vente:
            texte += "\n>>> VENTE à " + str(prix) + "\n"
            gain = (prix - prix_achat_reel) * (montant_usdc_initial / prix_achat_reel)
            profit_net += gain

            place_order("sell", montant_xrp)

            texte += "Profit trade : " + str(round(gain, 4)) + " USDC\n"
            texte += "Nouveau profit net : " + str(round(profit_net, 4)) + " USDC\n"

            position = 0

            if snowball:
                montant_usdc += gain
                texte += "\nBOULE DE NEIGE ACTIVÉE\n"
                texte += "Nouveau montant USDC : " + str(round(montant_usdc, 4)) + "\n"

        log.text(texte)
        time.sleep(3)

st.title("BOT XRP Kraken – Profit Net + Boule de Neige")

solde_usdc = get_usdc_balance()
st.info("Solde USDC disponible sur Kraken : " + str(solde_usdc) + " USDC")

prix_achat = st.number_input("Prix d'achat (USD)", min_value=0.0)
prix_vente = st.number_input("Prix de vente (USD)", min_value=0.0)
montant_usdc = st.number_input("Montant USDC initial par trade", min_value=1.0)

snowball = st.checkbox("Activer la boule de neige (réinvestit le profit automatiquement)")

log = st.empty()
profit_display = st.empty()

col1, col2 = st.columns(2)
with col1:
    start = st.button("Démarrer le bot")
with col2:
    stop = st.button("STOP BOT")

if start and not running:
    t = threading.Thread(
        target=bot_thread,
        args=(prix_achat, prix_vente, montant_usdc, log, profit_display, snowball)
    )
    t.start()
    st.success("Bot lancé !")

if stop:
    running = False
    st.error("Bot arrêté ! Profit net final : " + str(round(profit_net, 4)) + " USDC")
