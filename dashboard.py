import streamlit as st
import krakenex
import time

# 1. CONNEXION (Vérifie tes secrets Kraken sur GitHub/Streamlit)
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

st.title("❄️ SNOWBALL XRP (29$ Start)")

# 2. TES RÉGLAGES (C'est ici que tu programmes tes entrées/sorties)
with st.container():
    st.subheader("🎯 Ta Stratégie")
    col1, col2 = st.columns(2)
    p_achat = col1.number_input("J'achète à (Prix Bas)", value=1.0200, format="%.4f")
    p_vente = col2.number_input("Je vends à (Prix Haut)", value=1.0600, format="%.4f")
    
    profit_theorique = ((p_vente / p_achat) - 1) * 100
    st.write(f"💰 Gain par cycle : **+{profit_theorique:.2f}%**")

# État du bot
if 'bot_actif' not in st.session_state: st.session_state.bot_actif = False

c_start, c_stop = st.columns(2)
if c_start.button("▶️ LANCER LA BOUCLE", use_container_width=True, type="primary"):
    st.session_state.bot_actif = True
if c_stop.button("⏹️ TOUT ARRÊTER", use_container_width=True):
    st.session_state.bot_actif = False
    st.rerun()

# 3. LA MÉCANIQUE AUTOMATIQUE
status = st.empty()

if st.session_state.bot_actif:
    while st.session_state.bot_actif:
        try:
            # On demande à Kraken s'il y a un ordre en cours
            ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})

            if not ordres:
                # --- PHASE RÉINVESTISSEMENT (BOULE DE NEIGE) ---
                # On regarde tes 29$ (ou ce qu'il en reste avec le profit)
                bal = k.query_private('Balance')['result']
                cash_dispo = float(bal.get('USDC', 0))
                
                # On calcule combien de XRP on achète (on garde 1.5% pour les frais Kraken)
                volume_xrp = (cash_dispo * 0.985) / p_achat
                
                if volume_xrp >= 10: # Minimum de sécurité Kraken
                    status.success(f"🔄 Cycle lancé : Achat de {volume_xrp:.2f} XRP à {p_achat}$")
                    
                    # On envoie l'ordre d'achat + la revente automatique (Close)
                    params = {
                        'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
                        'price': str(round(p_achat, 4)), 'volume': str(round(volume_xrp, 1)),
                        'close[ordertype]': 'limit', 'close[price]': str(round(p_vente, 4)), 'close[type]': 'sell'
                    }
                    k.query_private('AddOrder', params)
                else:
                    status.error(f"Solde insuffisant ({cash_dispo:.2f} USDC). Besoin d'au moins 10 XRP.")
                    st.session_state.bot_actif = False
                    break
            else:
                # Le bot attend que le prix touche tes cibles
                for oid, det in ordres.items():
                    status.info(f"⏳ En attente : {det['descr']['order']}")

        except Exception as e:
            status.error(f"Erreur API : {e}")

        time.sleep(20) # Scan toutes les 20 secondes
        st.rerun()
