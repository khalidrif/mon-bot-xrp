import streamlit as st
import ccxt
import time

st.set_page_config(page_title="Test Ordre Kraken", page_icon="🧪")
st.title("🧪 Testeur d'Ordre XRP/USDC")

# 1. Connexion API avec correction Nonce
try:
    exchange = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
        'options': {'nonce': lambda: int(time.time() * 1000)}
    })
    st.success("✅ API Connectée")
except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")
    st.stop()

# 2. Vérification précise du portefeuille
if st.button("🔎 Étape 1 : Vérifier mes soldes réels"):
    try:
        balance = exchange.fetch_balance()
        # On filtre pour ne voir que ce que tu possèdes vraiment
        possessions = {k: v for k, v in balance['total'].items() if v > 0}
        st.write("Voici ce que le bot voit sur ton compte :")
        st.json(possessions)
        
        if 'USDC' not in possessions:
            st.warning("⚠️ Attention : Tu n'as pas de USDC. Convertis tes USD ou EUR en USDC sur Kraken.")
    except Exception as e:
        st.error(f"Erreur lecture solde : {e}")

# 3. Test d'envoi d'ordre
st.divider()
st.subheader("Étape 2 : Envoyer un ordre test")
montant_test = st.number_input("Montant de XRP à tester (Min 15 recommandé)", value=20.0)

if st.button("🚀 LANCER L'ORDRE D'ACHAT MAINTENANT"):
    try:
        st.info(f"Tentative d'achat au marché de {montant_test} XRP...")
        
        # On tente l'achat immédiat au prix du marché
        ordre = exchange.create_market_buy_order('XRP/USDC', montant_test)
        
        st.success("🎉 SUCCÈS ! L'ordre a été accepté par Kraken.")
        st.write("Détails de l'ordre :")
        st.json(ordre)
        
    except ccxt.InsufficientFunds as e:
        st.error(f"❌ FONDS INSUFFISANTS : Tu n'as pas assez de USDC (frais inclus).")
        st.info("Astuce : Essaie de diminuer le montant de XRP ou d'ajouter des USDC.")
    except ccxt.InvalidOrder as e:
        st.error(f"❌ ORDRE INVALIDE : {e}")
        st.info("Souvent dû à un montant trop petit (Kraken demande ~10-15 XRP minimum).")
    except ccxt.AuthenticationError as e:
        st.error(f"❌ ERREUR API : Tes clés n'ont pas les permissions 'Trading'.")
    except Exception as e:
        st.error(f"❌ ERREUR INCONNUE : {e}")

st.divider()
st.caption("Note : Ce bouton achète REELLEMENT du XRP si le test réussit.")
