import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Kraken XRP Sniper", page_icon="🎯")
st.title("🎯 Bot XRP/USDC : Achat & Vente")

# 1. Connexion API
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'fetchCurrencies': True} # Aide à la précision des prix
    })
    # Vérification du solde pour confirmer la connexion
    balance = exchange.fetch_balance()
    usdc_balance = balance.get('USDC', {}).get('free', 0)
    st.success(f"✅ Connecté ! Solde disponible : {usdc_balance:.2f} USDC")
except Exception as e:
    st.error(f"Erreur : {e}")
    st.stop()

# 2. Paramètres
st.subheader("Configuration")
col1, col2, col3 = st.columns(3)
with col1:
    p_achat = st.number_input("Prix Achat (USDC)", value=1.3000, format="%.4f")
with col2:
    p_vente = st.number_input("Prix Vente (USDC)", value=1.3500, format="%.4f")
with col3:
    montant = st.number_input("Montant (XRP)", value=20.0, step=1.0)

# 3. Exécution
if st.button("🚀 Activer le Bot"):
    status = st.empty()
    prix_live = st.empty()
    
    # ÉTAPE 1 : ACHAT
    etape = "ACHAT"
    while etape == "ACHAT":
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            actuel = ticker['last']
            prix_live.metric("Prix Actuel", f"{actuel} USDC", f"Cible Achat: {p_achat}")

            if actuel <= p_achat:
                status.warning("⚠️ Tentative d'ACHAT immédiate...")
                # EXECUTION RÉELLE
                ordre = exchange.create_market_buy_order('XRP/USDC', montant)
                st.write("Détails Ordre Achat :", ordre)
                etape = "VENTE"
            else:
                status.info(f"⏳ Attente prix d'achat ({p_achat})...")
            time.sleep(10)
        except Exception as e:
            st.error(f"Erreur Achat : {e}")
            break

    # ÉTAPE 2 : VENTE
    while etape == "VENTE":
        try:
            ticker = exchange.fetch_ticker('XRP/USDC')
            actuel = ticker['last']
            prix_live.metric("Prix Actuel", f"{actuel} USDC", f"Cible Vente: {p_vente}")

            if actuel >= p_vente:
                status.warning("⚠️ Tentative de VENTE immédiate...")
                # EXECUTION RÉELLE
                ordre = exchange.create_market_sell_order('XRP/USDC', montant)
                st.write("Détails Ordre Vente :", ordre)
                st.balloons()
                etape = "FINI"
            else:
                status.info(f"🚀 XRP en main. Attente vente ({p_vente})...")
            time.sleep(10)
        except Exception as e:
            st.error(f"Erreur Vente : {e}")
            break
