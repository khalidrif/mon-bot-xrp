import streamlit as st
import requests
import time

# Configuration de la page
st.set_page_config(page_title="XRP LIVE", layout="centered")

# Fonction pour récupérer le prix public (sans API Key)
def get_xrp_price():
    try:
        url = "https://api.kraken.com"
        response = requests.get(url).json()
        price = response['result']['XRPUSDC']['c'][0]
        return float(price)
    except:
        return None

# Affichage minimaliste
st.title("🪙 XRP Price")

# Conteneur pour le rafraîchissement
placeholder = st.empty()

while True:
    price = get_xrp_price()
    with placeholder.container():
        if price:
            st.metric(label="Kraken XRP/USDC", value=f"{price:.4f} $")
        else:
            st.write("Connexion en cours...")
    
    # Pause de 10 secondes avant de recharger le prix
    time.sleep(10)
