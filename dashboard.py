import streamlit as st
import krakenex
import time

# 1. CONNEXION
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

st.set_page_config(page_title="XRP Snowball Bot")
st.title("❄️ XRP BOULE DE NEIGE")

# 2. RÉGLAGES DU BOT
with st.sidebar:
    st.header("Paramètres")
    p_achat = st.number_input("Prix d'Achat", value=1.0500, format="%.4f")
    p_vente = st.number_input("Prix de Vente", value=1.1000, format="%.4f")
    vol_initial = st.number_input("Volume Initial (XRP)", value=20.0)
    st.info("Le bot réinvestit tout le profit automatiquement.")

if 'running' not in st.session_state:
    st.session_state.running = False
if 'cycles' not in st.session_state:
    st.session_state.cycles = 0

# 3. CONTRÔLE
c1, c2 = st.columns(2)
if c1.button("▶️ DÉMARRER LE SNOWBALL"):
    st.session_state.running = True
if c2.button("⏹️ ARRÊTER"):
    st.session_state.running = False

# 4. LOGIQUE DE LA BOUCLE
status = st.empty()

if st.session_state.running:
    while st.session_state.running:
        try:
            # On regarde s'il y a un ordre en cours
            res = k.query_private('OpenOrders')
            ordres = res.get('result', {}).get('open', {})

            if not ordres:
                # Étape Boule de Neige : On calcule le nouveau volume
                # On regarde le solde USDC disponible
                bal = k.query_private('Balance')['result']
                usdc_dispo = float(bal.get('USDC', 0))
                
                # On calcule combien on peut acheter avec TOUT l'USDC (moins 1% pour les frais)
                nouveau_vol = (usdc_dispo * 0.99) / p_achat
                
                if nouveau_vol < 10: # Minimum Kraken
                    nouveau_vol = vol_initial
                
                status.success(f"🔄 Lancement Cycle #{st.session_state.cycles + 1}")
                status.write(f"Volume réinvesti : **{nouveau_vol:.2f} XRP**")
                
                # Placement de l'ordre Achat -> Vente
                params = {
                    'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
                    'price': str(round(p_achat, 4)), 'volume': str(round(nouveau_vol, 1)),
                    'close[ordertype]': 'limit', 'close[price]': str(round(p_vente, 4)), 'close[type]': 'sell'
                }
                k.query_private('AddOrder', params)
                st.session_state.cycles += 1
                
            else:
                for oid, det in ordres.items():
                    status.info(f"⏳ Cycle {st.session_state.cycles} en cours : {det['descr']['order']}")

        except Exception as e:
            status.error(f"Erreur : {e}")

        time.sleep(15) # Attend 15 sec avant de revérifier
        st.rerun()

else:
    status.write("💤 Bot à l'arrêt.")
