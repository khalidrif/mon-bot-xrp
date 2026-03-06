import streamlit as st
import requests
import time

# 1. Look minimaliste
st.set_page_config(page_title="XRP PRICE", layout="centered")

# 2. Fonction pour lire le prix sur Kraken (Public)
def get_price():
    try:
        url = "https://api.kraken.com"
        res = requests.get(url).json()
        return float(res['result']['XRPUSDC']['c'][0])
    except:
        return None

# 3. Affichage unique
placeholder = st.empty()

while True:
    px = get_price()
    with placeholder.container():
        if px:
            # Affiche juste le prix en très gros
            st.write(f"# {px:.4f} $")
        else:
            st.write("Connexion...")
    
    # Mise à jour toutes les 5 secondes
    time.sleep(5)
