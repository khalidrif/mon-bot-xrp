import streamlit as st
import ccxt
import time

st.title("🤖 XRP Boule de Neige (USDC)")

# --- CONFIGURATION ---
col1, col2 = st.columns(2)
buy_p = col1.number_input("Prix d'Achat (USD)", value=1.3640, format="%.4f")
sell_p = col2.number_input("Prix de Vente (USD)", value=1.3850, format="%.4f")

# Utilisation d'une "key" pour que Streamlit détecte le changement immédiatement
usdc_saisi = st.number_input("Montant de départ (USDC)", value=100.0, step=10.0, key="input_usdc")

# Initialisation/Mise à jour du capital de session
if 'current_usdc' not in st.session_state or st.sidebar.button("Réinitialiser avec le nouveau montant"):
    st.session_state.current_usdc = usdc_saisi
    st.session_state.total_gain_usdc = 0.0

# --- AFFICHAGE ---
st.write("---")
c1, c2 = st.columns(2)
c1.metric("Capital Actuel", f"{st.session_state.current_usdc:.2f} USDC")
c2.metric("Gain Net Accumulé", f"+{st.session_state.total_gain_usdc:.2f} USDC")

# --- SÉCURITÉ FRAIS ---
frais = 0.0026
seuil = (buy_p * (1 + frais)) / (1 - frais)

if sell_p <= seuil:
    st.error(f"❌ Vente trop basse ! Minimum requis : {seuil:.4f}")
    lancer = False
else:
    st.success("✅ Stratégie rentable")
    lancer = True

# --- BOUTON DE LANCEMENT ---
if lancer and st.button("🚀 LANCER LE BOT"):
    # On s'assure que le capital est bien celui saisi juste avant de lancer
    st.session_state.current_usdc = usdc_saisi 
    
    st.info(f"Démarrage avec {st.session_state.current_usdc} USDC...")
    
    # ... (Reste de la boucle while True identique au script précédent)
