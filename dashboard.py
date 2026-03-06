import streamlit as st
import krakenex

# 1. Configuration
st.set_page_config(page_title="XRP Command Center", layout="wide")
st.title("🎮 Centre de Contrôle XRP")

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    st.metric("Prix XRP actuel", f"{prix_actuel:.4f} USDC", delta="Marché en direct")
    
    res_open = k.query_private('OpenOrders')['result']['open']
except:
    st.error("Connexion Kraken impossible (Vérifie tes clés ou la maintenance).")
    res_open = {}

# 4. Zone de Lancement (Design épuré)
with st.expander("🚀 LANCER UN NOUVEAU BOT", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    p_in = col1.number_input("ACHAT (Bas)", value=1.0400, format="%.4f")
    p_out = col2.number_input("VENTE (Haut)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité XRP", value=12.0)
    
    if col4.button("⚡ ACTIVER", use_container_width=True):
        try:
            # On stocke le prix d'entrée dans userref (multiplié par 1000)
            memo = int(p_in * 1000)
            order_data = {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(vol),
                'userref': str(memo),
                'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
            }
            k.query_private('AddOrder', order_data)
            st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

st.write("---")

# 5. Le Mur des Bots (Affichage par Cartes)
st.subheader(f"🤖 Mes Bots Actifs ({len(res_open)})")

if res_open:
    # On crée une grille de 3 colonnes pour les cartes
    cols = st.columns(3)
    for i, (oid, det) in enumerate(res_open.items()):
        with cols[i % 3]:
            type_o = det['descr']['type'].upper()
            prix_o = float(det['descr']['price'])
            
            # Récupération du prix d'entrée mémorisé
            try:
                p_in_memo = int(det.get('userref', 0)) / 1000
            except: p_in_memo = 0.0

            # Design de la carte
            color = "green" if type_o == "BUY" else "red"
            emoji = "📥" if type_o == "BUY" else "💰"
            
            with st.container(border=True):
                st.markdown(f"### {emoji} Bot {i+1}")
                if type_o == "BUY":
                    st.write(f"**Objectif :** Acheter à **{prix_o:.4f}**")
                    st.write(f"**Sortie prévue :** {p_out if 'p_out' in locals() else '---'}")
                else:
                    st.write(f"✅ **Acheté à :** {p_in_memo:.4f}")
                    st.write(f"🎯 **Cible Vente :** **{prix_o:.4f}**")
                
                st.write(f"💎 **Valeur :** {prix_o * float(det['vol']):.2f} USDC")
                
                # Bouton STOP unique pour ce bot
                if st.button(f"❌ STOP BOT {i+1}", key=oid):
                    k.query_private('CancelOrder', {'txid': oid})
                    st.rerun()
else:
    st.info("Aucun bot ne tourne. C'est le moment d'en lancer un !")

# 6. Bouton de secours
if st.sidebar.button("🗑️ TOUT ANNULER"):
    k.query_private('CancelAll')
    st.rerun()
