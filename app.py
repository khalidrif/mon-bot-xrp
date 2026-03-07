import streamlit as st
import time
import krakenex

# -------------------------------
# INTERFACE STREAMLIT
# -------------------------------

st.title("BOT XRP Kraken – Achat / Vente Infinie (1 SEUL FICHIER)")

st.write("Configure ton bot :")

prix_achat = st.number_input("Prix d'achat (USD)", min_value=0.0)
prix_vente = st.number_input("Prix de vente (USD)", min_value=0.0)
montant = st.number_input("Montant en XRP", min_value=0.0)

run_bot = st.button("Démarrer le bot")

# -------------------------------
# SI L'UTILISATEUR APPUIE SUR START
# -------------------------------
if run_bot:

    st.success("Bot démarré ! Il tourne en direct ci‑dessous.")
    st.write("Vous pouvez laisser cette page ouverte.")

    # -------------------------------
    # CONNEXION API KRAKEN
    # -------------------------------
    api = krakenex.API()
    api.load_key('kraken.key')

    # Récupération du prix
    def get_price():
        data = api.query_public('Ticker', {'pair': 'XRPUSD'})
        return float(data['result']['XXRPZUSD']['c'][0])

    # Ordre Kraken
    def place_order(order_type, volume):
        return api.query_private('AddOrder', {
            'pair': 'XRPUSD',
            'type': order_type,
            'ordertype': 'market',
            'volume': volume
        })

    position = 0  # 0 = pas d'XRP, 1 = XRP en portefeuille

    # Zone d’affichage live
    log = st.empty()

    # -------------------------------
    # BOUCLE INFINIE
    # -------------------------------
    while True:
        prix = get_price()

        texte = f"Prix actuel XRP : {prix}\n"

        # Achat
        if position == 0 and prix <= prix_achat:
            texte += f"\n>>> Achat de {montant} XRP au prix {prix}\n"
            res = place_order("buy", montant)
            texte += str(res)
            position = 1

        # Vente
        elif position == 1 and prix >= prix_vente:
            texte += f"\n>>> Vente de {montant} XRP au prix {prix}\n"
            res = place_order("sell", montant)
            texte += str(res)
            position = 0

        log.text(texte)
        time.sleep(3)
