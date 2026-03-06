import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="XRP Command Center", layout="wide")
st.title("🎮 Centre de Contrôle XRP")

# Initialisation de la sécurité anti-doublon
if 'dernier_ordre' not in st.session_state:
    st.session_state.dernier_ordre = None

# 2. Connexion API
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Récupération des données (Prix et Ordres)
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    # Correction de l'erreur 'result' et extraction du prix propre
    if 'result' in ticker:
        prix_actuel = float(ticker['result']['XRPUSDC']['c'][0])
        st.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    else:
        st.error("Kraken ne répond pas (Maintenance ?)")
        prix_actuel = 1.40

    # Récupération des ordres ouverts
    res_open = k.query_private('OpenOrders')
    ordres_ouverts = res_open.get('result', {}).get('open', {})
    
except Exception as e:
    st.warning(f"Connexion en attente... {e}")
    ordres_ouverts = {}

# 4. Zone de Lancement (Design épuré)
with st.expander("🚀 LANCER UN NOUVEAU BOT", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    p_in = col1.number_input("ACHAT (Bas)", value=1.0400, format="%.4f")
    p_out = col2.number_input("VENTE (Haut)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité XRP", value=12.0)
    
    if col4.button("⚡ ACTIVER", use_container_width=True):
        # SECURITÉ ANTI-DOUBLE : On vérifie si l'ordre est identique au précédent
        id_tentative = f"{p_in}-{p_out}-{vol}"
        
        if st.session_state.dernier_ordre == id_tentative:
            st.warning("⚠️ Ordre déjà envoyé (Doublon bloqué)")
        else:
            try:
                # On multiplie par 1000 pour stocker le prix d'entrée dans userref
                memo_prix = int(p_in * 1000)
                
                res = k.query_private('AddOrder', {
                    'pair': 'XRPUSDC',
                    'type': 'buy',
                    'ordertype': 'limit',
                    'price': str(p_in),
                    'volume': str(vol),
                    'userref': str(memo_prix),
                    'close[ordertype]': 'limit',
                    'close[price]': str(p_out),
                    'close[type]': 'sell'
                })
                
                if res.get('result'):
                    st.session_state.dernier_ordre = id_tentative
                    st.success("✅ Bot activé avec succès !")
                    st.rerun()
                else:
                    st.error(f"Erreur Kraken : {res.get('error')}")
            except Exception as e:
                st.error(f"Erreur technique : {e}")

st.write("---")

# 5. Le Mur des Bots (Affichage par Cartes)
st.subheader(f"🤖 Mes Bots Actifs ({len(ordres_ouverts)})")

if ordres_ouverts:
    cols = st.columns(3) # Affiche 3 cartes par ligne
    for i, (oid, det) in enumerate(ordres_ouverts.items()):
        with cols[i % 3]:
            type_o = det['descr']['type'].upper()
            prix_o = float(det['descr']['price'])
            vol_o = float(det['vol'])
            
            # Récupération du prix d'entrée mémorisé dans userref
            try:
                p_in_memo = int(det.get('userref', 0)) / 1000
            except:
                p_in_memo = 0.0

            # Couleur et icône
            emoji = "🟢" if type_o == "BUY" else "🔴"
            
            # Affichage de la carte
            st.markdown(f"### {emoji} Bot {i+1}")
            if type_o == "BUY":
                st.info(f"**EN ATTENTE ACHAT**\n\nCible : **{prix_o:.4f}**")
            else:
                st.success(f"**EN ATTENTE VENTE**\n\nAcheté à : **{p_in_memo:.4f} ✅**\n\nObjectif : **{prix_o:.4f}**")
            
            st.write(f"💎 Valeur : **{prix_o * vol_o:.2f} USDC**")
            
            # Bouton STOP individuel
            if st.button(f"❌ STOP BOT {i+1}", key=oid):
                k.query_private('CancelOrder', {'txid': oid})
                st.rerun()
else:
    st.info("Aucun bot actif. Ton argent est disponible dans ton solde Kraken.")

# 6. RESET TOTAL (Dans la barre latérale pour ne pas cliquer par erreur)
if st.sidebar.button("🗑️ TOUT ANNULER"):
    k.query_private('CancelAll')
    st.rerun()
