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
    # On extrait le prix actuel (premier élément de la liste 'c')
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    st.metric("Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    
    res_open = k.query_private('OpenOrders')['result']['open']
except Exception as e:
    st.error(f"Connexion Kraken impossible : {e}")
    res_open = {}

# 4. Zone de Lancement
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

# 5. Affichage par Cartes (Simplifié pour éviter l'erreur)
st.subheader(f"🤖 Mes Bots Actifs ({len(res_open)})")

if res_open:
    cols = st.columns(3)
    for i, (oid, det) in enumerate(res_open.items()):
        with cols[i % 3]:
            type_o = det['descr']['type'].upper()
            prix_o = float(det['descr']['price'])
            vol_o = float(det['vol'])
            
            # Récupération du prix d'entrée mémorisé
            try:
                p_in_memo = int(det.get('userref', 0)) / 1000
            except: 
                p_in_memo = 0.0

            # Style visuel
            color = "🟢" if type_o == "BUY" else "🔴"
            
            # Remplacement de st.container(border=True) par une box simple
            st.markdown(f"""
            ---
            ### {color} Bot {i+1}
            **Type :** {"ACHAT" if type_o == "BUY" else "VENTE"}
            """)
            
            if type_o == "BUY":
                st.write(f"**Objectif :** Acheter à **{prix_o:.4f}**")
            else:
                st.write(f"✅ **Acheté à :** {p_in_memo:.4f}")
                st.write(f"🎯 **Cible Vente :** **{prix_o:.4f}**")
            
            st.write(f"💎 **Valeur :** {prix_o * vol_o:.2f} USDC")
            
            # Bouton STOP unique
            if st.button(f"❌ ARRÊTER BOT {i+1}", key=oid):
                k.query_private('CancelOrder', {'txid': oid})
                st.rerun()
else:
    st.info("Aucun bot actif.")

# 6. Bouton de secours
st.write("---")
if st.button("🗑️ TOUT ANNULER"):
    k.query_private('CancelAll')
    st.rerun()
