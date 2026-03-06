import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="XRP Snowball Color", layout="wide")
st.title("❄️ XRP Snowball : Console en Couleurs")

if 'profit_cumule' not in st.session_state:
    st.session_state.profit_cumule = 0.0

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Récupération des données
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    
    res_open = k.query_private('OpenOrders')['result']['open']
    prix_deja_poses = [float(det['descr']['price']) for det in res_open.values()]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    c2.metric("💰 Profit Cumulé", f"+{st.session_state.profit_cumule:.4f} USDC")
    c3.metric("🤖 Bots Actifs", len(res_open))

except Exception as e:
    st.error(f"Erreur : {e}")
    prix_actuel = 1.40
    res_open = {}
    prix_deja_poses = []

# 4. Formulaire de lancement
st.write("---")
with st.form("form_bot"):
    st.subheader("➕ Lancer un Bot (Ex: Achat 1.5 / Vente 1.9)")
    col1, col2, col3 = st.columns(3)
    p_achat = col1.number_input("Prix d'ACHAT (USDC)", value=1.5000, format="%.4f")
    p_vente = col2.number_input("Prix de VENTE (USDC)", value=1.9000, format="%.4f")
    vol = col3.number_input("Volume (XRP)", value=12.0)
    
    frais = (p_achat * vol * 0.0026) + (p_vente * vol * 0.0026)
    gain_net = ((p_vente - p_achat) * vol) - frais
    st.info(f"📈 Prévision : **+{gain_net:.2f} USDC** de profit net.")
    
    submit = st.form_submit_button("🚀 ACTIVER LE BOT")

if submit:
    if any(abs(p - p_achat) < 0.0001 for p in prix_deja_poses):
        st.warning(f"⚠️ Déjà un bot à ce prix !")
    else:
        try:
            order_data = {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
                'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
            }
            k.query_private('AddOrder', order_data)
            st.session_state.profit_cumule += gain_net
            st.success("✅ Bot ajouté !")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur Kraken : {e}")

# 5. TABLEAU COLORÉ (Vert et Rouge)
st.write("---")
st.subheader("📦 Ma Grille de Trading")

if res_open:
    liste_affichage = []
    for oid, det in res_open.items():
        t = det['descr']['type'].upper()
        liste_affichage.append({
            "ID": oid[:6],
            "Type": "📥 ACHAT" if t == "BUY" else "💰 VENTE",
            "Prix Cible": float(det['descr']['price']),
            "Quantité": float(det['vol']),
            "Couleur": "background-color: #2ecc71; color: white" if t == "BUY" else "background-color: #e74c3c; color: white"
        })
    
    df = pd.DataFrame(liste_affichage)

    # Fonction pour appliquer les couleurs par ligne
    def colorer_ligne(row):
        return [row['Couleur']] * len(row)

    # Affichage du tableau avec style
    st.dataframe(df.style.apply(colorer_ligne, axis=1).hide(axis='index'), use_container_width=True)
else:
    st.info("Aucun bot actif.")

if st.sidebar.button("🗑️ RESET TOTAL"):
    k.query_private('CancelAll')
    st.session_state.profit_cumule = 0.0
    st.rerun()
