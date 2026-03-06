import streamlit as st
import krakenex
import pandas as pd

st.set_page_config(page_title="Kraken Snowball Bot", layout="wide")
st.title("❄️ Bot XRP : Effet Boule de Neige")

# 1. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 2. Récupérer les données
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    # Correction de l'extraction du prix (on prend le premier élément de la liste 'c')
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    st.metric("Prix XRP actuel", f"{prix_actuel} USDC")
    
    res_open = k.query_private('OpenOrders')['result']['open']
    prix_deja_poses = [float(det['descr']['price']) for det in res_open.values()]
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    prix_actuel = 1.40
    res_open = {}
    prix_deja_poses = []

# 3. CALCULATEUR DE GAIN (Visualisation avant de lancer)
with st.form("bot_individuel"):
    st.write("### ➕ Configurer un Bot Boule de Neige")
    c1, c2, c3 = st.columns(3)
    p_achat = c1.number_input("Prix d'ACHAT", value=round(prix_actuel*0.99, 4), format="%.4f")
    p_vente = c2.number_input("Prix de VENTE", value=round(prix_actuel*1.02, 4), format="%.4f")
    vol = c3.number_input("Volume (XRP)", value=15.0)
    
    # Calcul du gain net estimé (0.26% de frais Kraken par défaut)
    frais = (p_achat * vol * 0.0026) + (p_vente * vol * 0.0026)
    gain_brut = (p_vente - p_achat) * vol
    gain_net = gain_brut - frais
    
    st.info(f"💰 Gain Net Estimé : **+{gain_net:.2f} USDC** (après frais)")
    
    submit = st.form_submit_button("🚀 LANCER LA BOULE DE NEIGE")

# 4. LOGIQUE D'ENVOI
if submit:
    if any(abs(p - p_achat) < 0.0001 for p in prix_deja_poses):
        st.warning(f"⚠️ Prix déjà couvert à {p_achat}")
    else:
        try:
            order_data = {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
                'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
            }
            k.query_private('AddOrder', order_data)
            st.success(f"✅ Bot lancé ! Objectif : +{gain_net:.2f} USDC")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur Kraken : {e}")

# 5. AFFICHAGE DE LA LISTE AVEC GAIN ATTENDU
st.write("---")
st.subheader(f"📋 Mes Bots en attente ({len(res_open)})")
if res_open:
    data_display = []
    for oid, det in res_open.items():
        p = float(det['descr']['price'])
        v = float(det['vol'])
        # On affiche le gain si cet ordre se clôture
        data_display.append({
            "ID": oid[:6],
            "Type": det['descr']['type'].upper(),
            "Prix": p,
            "Volume": v,
            "Profit Attendu": "Calculé à la vente" if det['descr']['type'] == 'buy' else f"{(p - p_achat) * v:.2f} USDC"
        })
    st.dataframe(pd.DataFrame(data_display), use_container_width=True)
else:
    st.info("Aucun bot actif.")

if st.button("🗑️ TOUT ANNULER"):
    k.query_private('CancelAll')
    st.rerun()
