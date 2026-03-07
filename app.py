import streamlit as st
import time
import krakenex
import threading

# -------------------------------------------------------
# VARIABLES GLOBALES
# -------------------------------------------------------
running = False
profit_net = 0.0

# -------------------------------------------------------
# CONFIGURATION API KRAKEN (via Secrets Streamlit)
# -------------------------------------------------------
api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

# -------------------------------------------------------
# FONCTIONS KRAKEN
# -------------------------------------------------------
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

# -------------------------------------------------------
# THREAD DU BOT
# -------------------------------------------------------
def bot_thread(prix_achat, prix_vente, montant_usdc, log):
    global running, profit_net
    running = True
    position = 0
    prix_achat_reel = 0

    while running:
        prix = get_price()
        montant_xrp = montant_usdc / prix

        texte = f"Prix XRP : {prix}\n"
        texte += f"Montant : {montant_usdc} USDC → {montant_xrp:.4f} XRP\n"
        texte += f"Profit net actuel : {profit_net:.4f} USDC\n"

        # Achat
        if position == 0 and prix <= prix_achat:
            texte += f"\n>>> ACHAT de {montant_xrp:.4f} XRP à {prix}\n"
            prix_achat_reel = prix
            place_order("buy", montant_xrp)
            position = 1

        # Vente
        elif position == 1 and prix >= prix_vente:
            texte += f"\n>>> VENTE de {montant_xrp:.4f} XRP à {prix}\n"

            gain = (prix - prix_achat_reel) * (montant_usdc / prix_achat_reel)
            profit_net += gain

            place_order("sell", montant_xrp)

            texte += f"Profit trade : {gain:.4f} USDC\n"
            texte += f"Profit net total : {profit_net:.4f} USDC\n"
            position = 0

        log.text(texte)
        time.sleep(3)

# -------------------------------------------------------
# INTERFACE STREAMLIT
# -------------------------------------------------------
st.title("BOT XRP Kraken – Achat/Vente Infinie + STOP + Profit")

# Affichage du solde USDC
solde_usdc = get_usdc_balance()
st.info(f"Solde USDC disponible sur Kraken : {solde_usdc} USDC")

# Paramètres utilisateur
prix_achat = st.number_input("Prix d'achat (USD)", min_value=0.0)
prix_vente = st.number_input("Prix de vente (USD)", min_value=0.0)
montant_usdc = st.number_input("Montant par trade (USDC)", min_value=0.0)

log = st.empty()

col1, col2 = st.columns(2)
with col1:
    start = st.button("Démarrer le bot")
with col2:
    stop = st.button("STOP BOT")

# Lancer le bot
if start and not running:
    t = threading.Thread(target=bot_thread, args=(prix_achat, prix_vente, montant_usdc, log))
    t.start()
    st.success("Bot lancé !")

# Stopper le bot
if stop:
    running = False
    st.error(f"Bot arrêté ! Profit net final : {profit_net:.4f} USDC")
