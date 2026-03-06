import streamlit as st
import krakenex
import pandas as pd

st.set_page_config(page_title="Kraken Multi-Bot", layout="wide")
st.title("🎛️ Console de Pilotage Multi-Bots (Individuels)")

# 1. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 2. Infos Marché
res = k.query_public('Ticker', {'pair': 'XRPUSDC'})
prix_actuel = float(res['result']['XRPUSDC']['c'][0])
st.metric("Prix XRP actuel", f"{prix_actuel} USDC")

# 3. Formulaire pour 1 Bot Spécifique
with st.expander("➕ Créer un nouveau Bot (Achat + Vente)", expanded=True):
    c1, c2, c3 = st.columns(3)
    p_achat = c1.number_input("Prix d'ACHAT (Limit)", value=round(prix_actuel * 0.98, 4), format="%.4f")
    p_vente = c2.number_input("Prix de VENTE (Limit)", value=round(prix_actuel * 1.02, 4), format="%.4f")
    vol = c3.number_input("Quantité (XRP)", value=15.0, step=1.0)
    
    if st.button("🚀 LANCER CE BOT"):
        try:
            # Ordre d'achat
            o_buy = k.query_private('AddOrder', {'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol)})
            # Ordre de vente
            o_sell = k.query_private('AddOrder', {'pair': 'XRPUSDC', 'type': 'sell', 'ordertype': 'limit', 'price': str(p_vente), 'volume': str(vol)})
            st.success(f"✅ Bot Activé : Achat {p_achat} / Vente {p_vente}")
        except Exception as e:
            st.error(f"Erreur : {e}")

# 4. Liste des ordres séparés
st.write("---")
st.write("### 📋 Liste de mes ordres actifs (Grille)")
try:
    res_orders = k.query_private('OpenOrders')['result']['open']
    if res_orders:
        data = []
        for oid, det in res_orders.items():
            data.append({
                "ID": oid,
                "Type": det['descr']['type'].upper(),
                "Prix": det['descr']['price'],
                "Volume": det['vol'],
                "Statut": det['status']
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Option pour tout annuler
        if st.button("🗑️ ANNULER TOUS LES ORDRES"):
            for oid in res_orders.keys():
                k.query_private('CancelOrder', {'txid': oid})
            st.warning("Tous les ordres ont été annulés.")
            st.rerun()
    else:
        st.info("Aucun bot ne tourne actuellement.")
except:
    st.info("En attente de données...")
