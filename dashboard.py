import streamlit as st
import krakenex
import pandas as pd

st.set_page_config(page_title="Kraken Smart-Bot", layout="wide")
st.title("🛡️ Console de Pilotage XRP")

# 1. Connexion (Récupère tes secrets Streamlit)
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 2. Récupérer le prix et les ordres pour la sécurité
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'])
    st.metric("Prix XRP actuel", f"{prix_actuel} USDC")
    
    res_open = k.query_private('OpenOrders')['result']['open']
    prix_deja_poses = [float(det['descr']['price']) for det in res_open.values()]
except Exception as e:
    st.error(f"Connexion Kraken impossible : {e}")
    res_open = {}
    prix_deja_poses = []

# 3. FORMULAIRE (Le bouton DOIT être à l'intérieur du 'with')
with st.form("bot_individuel"):
    st.write("### ➕ Ajouter un Bot Individuel")
    c1, c2, c3 = st.columns(3)
    p_achat = c1.number_input("Prix d'ACHAT", value=round(prix_actuel*0.99, 4), format="%.4f")
    p_vente = c2.number_input("Prix de VENTE", value=round(prix_actuel*1.02, 4), format="%.4f")
    vol = c3.number_input("Volume (XRP)", value=12.0)
    
    # LE BOUTON EST ICI (À l'intérieur du bloc with)
    submit = st.form_submit_button("🚀 LANCER CE BOT")

# 4. LOGIQUE APRÈS LE CLIC
if submit:
    if any(abs(p - p_achat) < 0.0001 for p in prix_deja_poses):
        st.warning(f"⚠️ Déjà un bot à {p_achat} USDC !")
    else:
        try:
            order_data = {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
                'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
            }
            k.query_private('AddOrder', order_data)
            st.success(f"✅ Bot ajouté à {p_achat}")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

# 5. LISTE DES BOTS
st.write("---")
st.subheader(f"📋 Bots actifs ({len(res_open)})")
if res_open:
    data = [{"ID": k[:6], "Type": v['descr']['type'], "Prix": v['descr']['price'], "Vol": v['vol']} for k, v in res_open.items()]
    st.dataframe(pd.DataFrame(data), use_container_width=True)
else:
    st.info("Aucun bot actif.")

if st.button("🗑️ TOUT ANNULER"):
    k.query_private('CancelAll')
    st.rerun()
