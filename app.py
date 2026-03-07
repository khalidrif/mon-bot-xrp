import streamlit as st
import ccxt
import time

st.title("🚀 Bot XRP Kraken : ORDRES RÉELS")

# --- CONNEXION ---
exchange = ccxt.kraken({
    'apiKey': st.secrets["KRAKEN_API_KEY"],
    'secret': st.secrets["KRAKEN_SECRET"],
    'enableRateLimit': True,
})

# --- CONFIGURATION ---
buy_p = st.number_input("Prix d'Achat (USD)", value=1.3640, format="%.4f")
sell_p = st.number_input("Prix de Vente (USD)", value=1.3850, format="%.4f")
usdc_saisi = st.number_input("Montant (USDC)", value=25.0)

# Initialisation session
if 'current_usdc' not in st.session_state:
    st.session_state.current_usdc = usdc_saisi

# --- LOGIQUE DE TRADING ---
if st.button("🚀 LANCER LES ORDRES RÉELS"):
    st.session_state.current_usdc = usdc_saisi
    st.warning("⚠️ Bot en ligne : Surveillance du marché...")

    while True:
        try:
            ticker = exchange.fetch_ticker('XRP/USD')
            prix_actuel = ticker['last']
            
            # 1. ACHAT RÉEL
            if prix_actuel <= buy_p:
                frais = 0.0026
                qty = (st.session_state.current_usdc * (1 - frais)) / buy_p
                
                st.write(f"🛒 Envoi ordre ACHAT : {qty:.2f} XRP à {buy_p}...")
                
                # --- LIGNE ACTIVE : PASSE L'ORDRE SUR KRAKEN ---
                ordre_achat = exchange.create_limit_buy_order('XRP/USD', qty, buy_p)
                st.success(f"Ordre Achat ID: {ordre_achat['id']}")

                # 2. ATTENTE VENTE
                while True:
                    p = exchange.fetch_ticker('XRP/USD')['last']
                    if p >= sell_p:
                        st.write(f"💰 Envoi ordre VENTE : {qty:.2f} XRP à {sell_p}...")
                        
                        # --- LIGNE ACTIVE : PASSE L'ORDRE SUR KRAKEN ---
                        ordre_vente = exchange.create_limit_sell_order('XRP/USD', qty, sell_p)
                        
                        # Mise à jour capital (Boule de neige)
                        nouveau_total = (qty * sell_p) * (1 - frais)
                        st.session_state.current_usdc = nouveau_total
                        st.success(f"Vente validée ID: {ordre_vente['id']}")
                        time.sleep(5)
                        st.rerun()
                        break
                    time.sleep(20)

            time.sleep(20)

        except Exception as e:
            st.error(f"Erreur Kraken : {e}")
            break
