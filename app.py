import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Kraken Order Bot", page_icon="💹")
st.title("💹 Bot Kraken : Exécuteur d'Ordre")

# 1. Connexion API (Nonce corrigé pour éviter les erreurs Kraken)
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: int(time.time() * 1000)}
    })
    # Vérification initiale du solde
    balance = exchange.fetch_balance()
    usdc_dispo = balance.get('USDC', {}).get('free', 0)
    st.sidebar.success(f"Connecté ! Solde : {usdc_dispo:.2f} USDC")
except Exception as e:
    st.error(f"Erreur de connexion API : {e}")
    st.stop()

# 2. Paramètres de l'ordre
st.subheader("⚙️ Réglages de l'ordre d'achat")
col1, col2 = st.columns(2)
prix_cible = col1.number_input("Acheter si le prix baisse à (USDC)", value=1.3000, format="%.4f")
montant_xrp = col2.number_input("Quantité de XRP à acheter", value=20.0, min_value=10.0)

# 3. Surveillance et Envoi
if st.button("▶️ DÉMARRER LA SURVEILLANCE"):
    info_zone = st.empty()
    prix_zone = st.empty()
    
    st.warning("⚠️ Ne fermez pas cette page. Le bot surveille le prix...")
    
    while True:
        try:
            # Récupérer le prix XRP/USDC en temps réel
            ticker = exchange.fetch_ticker('XRP/USDC')
            prix_actuel = ticker['last']
            
            # Affichage dynamique
            prix_zone.metric("Prix XRP actuel", f"{prix_actuel} USDC", f"Cible : {prix_cible}")
            info_zone.info(f"⏳ Attente... Prix actuel ({prix_actuel}) > Cible ({prix_cible})")

            # --- CONDITION D'ACHAT RÉELLE ---
            if prix_actuel <= prix_cible:
                info_zone.warning("🎯 CIBLE ATTEINTE ! Envoi de l'ordre d'achat à Kraken...")
                
                # EXECUTION DE L'ORDRE AU MARCHÉ
                ordre = exchange.create_market_buy_order('XRP/USDC', montant_xrp)
                
                # Confirmation
                st.success(f"✅ ORDRE EXÉCUTÉ ! ID: {ordre['id']}")
                st.balloons()
                st.json(ordre) # Affiche les détails (prix payé, frais, etc.)
                break # On arrête le bot après l'achat réussi
            
            time.sleep(5) # Vérification toutes les 5 secondes
            
        except Exception as e:
            st.error(f"❌ Erreur pendant la surveillance : {e}")
            break

st.divider()
st.caption("Note : Ce bot utilise des 'Market Orders'. Il achète immédiatement au meilleur prix dispo dès que la cible est touchée.")
