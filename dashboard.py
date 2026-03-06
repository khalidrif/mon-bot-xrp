import streamlit as st
import krakenex
import pandas as pd

st.set_page_config(page_title="Kraken Smart-Bot", layout="wide")
st.title("🛡️ Console de Pilotage avec Sécurité Anti-Double")

# 1. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 2. Récupérer les données du marché et des ordres
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'])
    st.metric("Prix XRP actuel", f"{prix_actuel} USDC")
    
    # On récupère les ordres déjà ouverts pour la sécurité
    res_open = k.query_private('OpenOrders')['result']['open']
    prix_deja_poses = [float(det['descr']['price']) for det in res_open.values()]
except:
    st.error("Connexion Kraken impossible.")
    res_open = {}
    prix_deja_poses = []

# 3. Formulaire de lancement avec SÉCURITÉ
with st.form("bot_securise"):
    st.write("### ➕ Ajouter un Bot Individuel")
    c1, c2, c3 = st.columns(3)
    p_achat = c1.number_input("Prix d'ACHAT", value=round(prix_actuel*0.99, 4), format="%.4f")
    p_vente = c2.number_input("Prix de VENTE", value=round(prix_actuel*1.02, 4), format="%.4f")
    vol = c3.number_input("Volume (XRP)", value=12.0)
    
    submit = st.form_submit_button("🚀 LANCER CE BOT")

if submit:
    # --- LA SÉCURITÉ ANTI-DOUBLE ---
    if any(abs(p - p_achat) < 0.0001 for p in prix_deja_poses):
        st.warning(f"⚠️ Action bloquée : Tu as déjà un bot actif au prix de {p_achat} USDC !")
    else:
        try:
            order_data = {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
                'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
            }
            k.query_private('AddOrder', order_data)
            st.success(f"✅ Nouveau Bot validé à {p_achat}")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

# 4. Affichage de la Liste propre
st.write("---")
st.subheader(f"📋 Bots en cours ({len(res_open)} actifs)")

if res_open:
    data_bots = []
    for oid, det in res_open.items():
        data_bots.append({
            "ID": oid[:6],
            "Type": det['descr']['type'].upper(),
            "Prix": det['descr']['price'],
            "Volume": det['vol'],
            "Ordre Complet": det['descr']['order']
        })
    st.dataframe(pd.DataFrame(data_bots), use_container_width=True)
else:
    st.info("Aucun bot actif.")

# 5. Bouton d'annulation globale
if st.button("🗑️ TOUT ANNULER POUR RECOMMENCER"):
    k.query_private('CancelAll')
    st.rerun()
