import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration et Connexion
st.set_page_config(page_title="Kraken Multi-Bot", layout="wide")
st.title("🎛️ Console de Pilotage Multi-Bots")

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 2. Infos Marché (Prix actuel)
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    st.metric("Prix XRP actuel", f"{prix_actuel} USDC")
except:
    st.error("Impossible de récupérer le prix actuel.")

# 3. Formulaire pour lancer 1 Bot (Achat -> Vente liée)
with st.expander("➕ Lancer un nouveau Bot (Individuel)", expanded=True):
    c1, c2, c3 = st.columns(3)
    p_achat = c1.number_input("Prix d'ACHAT", value=round(prix_actuel*0.99, 4), format="%.4f")
    p_vente = c2.number_input("Prix de VENTE", value=round(prix_actuel*1.02, 4), format="%.4f")
    vol = c3.number_input("Volume (XRP)", value=12.0)
    
    if st.button("🚀 LANCER CE BOT"):
        try:
            order_data = {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
                'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
            }
            k.query_private('AddOrder', order_data)
            st.success(f"✅ Bot ajouté : Achat {p_achat} / Vente {p_vente}")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

# 4. Affichage de la Liste des Bots Lancés
st.write("---")
st.subheader("📋 État de ma Grille (Bots en attente)")

try:
    res_orders = k.query_private('OpenOrders')['result']['open']
    if res_orders:
        data_bots = []
        for oid, det in res_orders.items():
            data_bots.append({
                "ID": oid[:8],
                "Type": det['descr']['type'].upper(),
                "Prix": det['descr']['price'],
                "Volume": det['vol'],
                "Description": det['descr']['order']
            })
        df = pd.DataFrame(data_bots)
        # Affichage sous forme de tableau propre
        st.dataframe(df, use_container_width=True)
        st.write(f"Total : **{len(res_orders)}** bots actifs.")
    else:
        st.info("Aucun bot actif sur Kraken.")
except Exception as e:
    st.info("Chargement des ordres...")

# 5. Bouton pour tout stopper
if st.button("🗑️ ANNULER TOUS LES BOTS"):
    k.query_private('CancelAll')
    st.warning("Ordres annulés.")
    st.rerun()
