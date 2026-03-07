import streamlit as st
import ccxt
import time
import pandas as pd

# 1. Connexion API Robuste
@st.cache_resource
def init_exchange():
    return ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: int(time.time() * 1000)}
    })

exchange = init_exchange()

st.title("🤖 XRP Sniper : Correcteur d'Ordres")

# --- ZONE DE DIAGNOSTIC ---
if st.sidebar.button("🔍 Diagnostiquer ma connexion"):
    try:
        # Test 1 : Permissions
        load = exchange.load_markets()
        st.sidebar.success("✅ Marchés chargés")
        
        # Test 2 : Solde
        bal = exchange.fetch_balance()
        usdc_free = bal.get('USDC', {}).get('free', 0)
        st.sidebar.write(f"Solde USDC libre : {usdc_free}")
        
        if usdc_free < 15:
            st.sidebar.error("❌ Solde USDC trop bas (Min 15 USDC requis)")
    except Exception as e:
        st.sidebar.error(f"❌ Erreur : {e}")

# --- PARAMÈTRES ---
budget_usdc = st.number_input("Budget (USDC)", value=20.0)
p_achat = st.number_input("Prix Achat Cible", value=1.3000, format="%.4f")

if st.button("▶️ LANCER LA SURVEILLANCE"):
    status = st.empty()
    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix = ticker['last']
            status.info(f"Prix actuel : {prix} | Cible : {p_achat}")

            if prix <= p_achat:
                status.warning("🎯 Cible atteinte ! Tentative d'envoi...")
                
                # --- LE CORRECTIF D'ORDRE ---
                # On utilise 'XRP/USDC' mais Kraken peut demander 'XRPUSDC' selon les comptes
                symbol = 'XRP/USDC' 
                amount = (budget_usdc * 0.99) / prix # On garde 1% pour les frais
                
                # Envoi avec capture d'erreur détaillée
                try:
                    ordre = exchange.create_market_buy_order(symbol, amount)
                    st.success(f"✅ ORDRE ACCEPTÉ ! ID: {ordre['id']}")
                    break
                except ccxt.InvalidOrder as e:
                    st.error(f"❌ Kraken refuse l'ordre : {e}. Vérifiez si le montant ({amount}) est suffisant.")
                    break
                except ccxt.InsufficientFunds:
                    st.error("❌ Pas assez de USDC (frais inclus). Baissez le montant ou ajoutez des USDC.")
                    break

            time.sleep(10)
        except Exception as e:
            st.error(f"Erreur réseau : {e}")
            break
