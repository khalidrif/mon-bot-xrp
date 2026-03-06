import streamlit as st
import krakenex
import time

# 1. CONNEXION
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

st.set_page_config(page_title="XRP Snowball Pro", layout="wide")
st.title("❄️ XRP SNOWBALL 29$")

# 2. CONFIGURATION DE TA STRATÉGIE
with st.container():
    st.subheader("🎯 Configure tes entrées")
    col1, col2 = st.columns(2)
    p_achat = col1.number_input("J'achète à (Prix Bas)", value=1.3600, format="%.4f", step=0.0001)
    p_vente = col2.number_input("Je vends à (Prix Haut)", value=1.4000, format="%.4f", step=0.0001)
    
    if p_vente <= p_achat:
        st.error("⚠️ ERREUR : Le prix de vente doit être plus haut que l'achat !")
        autorise_lancement = False
    else:
        profit_pct = ((p_vente / p_achat) - 1) * 100
        st.success(f"💰 Gain par cycle : **+{profit_pct:.2f}%**")
        autorise_lancement = True

# État du bot
if 'bot_run' not in st.session_state: st.session_state.bot_run = False

# 3. BOUTONS DE CONTRÔLE
c_start, c_stop = st.columns(2)

if c_start.button("▶️ LANCER LA BOUCLE", use_container_width=True, type="primary", disabled=not autorise_lancement):
    st.session_state.bot_run = True

if c_stop.button("⏹️ TOUT ARRÊTER & ANNULER SUR KRAKEN", use_container_width=True):
    st.session_state.bot_run = False
    try:
        k.query_private('CancelAll') # COMMANDE D'ANNULATION RÉELLE
        st.warning("Ordres annulés sur Kraken.")
    except:
        st.error("Erreur d'annulation API.")
    time.sleep(1)
    st.rerun()

# 4. LE MOTEUR AUTOMATIQUE
status = st.empty()

if st.session_state.bot_run:
    while st.session_state.bot_run:
        try:
            # Vérifier si un ordre existe déjà
            res_ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})

            if not res_ordres:
                # --- PHASE BOULE DE NEIGE ---
                # Récupérer ton solde (ex: 29$)
                bal = k.query_private('Balance')['result']
                cash = float(bal.get('USDC', 0))
                
                # Calcul du volume (On garde 1.5% pour les frais Kraken)
                volume_xrp = (cash * 0.985) / p_achat
                
                if volume_xrp >= 10: # Minimum Kraken
                    status.success(f"🔄 Nouveau cycle : Achat de {volume_xrp:.2f} XRP à {p_achat}$")
                    
                    # ENVOI DE L'ORDRE ACHAT + VENTE LIÉE
                    params = {
                        'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
                        'price': str(round(p_achat, 4)), 'volume': str(round(volume_xrp, 1)),
                        'close[ordertype]': 'limit', 'close[price]': str(round(p_vente, 4)), 'close[type]': 'sell'
                    }
                    k.query_private('AddOrder', params)
                else:
                    status.error(f"Solde insuffisant ({cash:.2f} USDC). Fin du bot.")
                    st.session_state.bot_run = False
                    break
            else:
                # Affichage de ce qui se passe sur Kraken
                for oid, det in res_ordres.items():
                    status.info(f"⏳ EN MISSION : {det['descr']['order']} (ID: {oid[:5]})")

        except Exception as e:
            status.error(f"Erreur API : {e}")

        time.sleep(15) # Scan toutes les 15 secondes
        st.rerun()

else:
    status.write("💤 Bot en sommeil. Configure tes prix et clique sur Lancer.")
