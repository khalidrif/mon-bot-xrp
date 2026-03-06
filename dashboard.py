import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration
st.set_page_config(page_title="XRP Snowball Color", layout="wide")
st.title("❄️ XRP Snowball : Console de Trading")

if 'profit_cumule' not in st.session_state:
    st.session_state.profit_cumule = 0.0

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    res_open = k.query_private('OpenOrders')['result']['open']
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    c2.metric("💰 Profit Cumulé", f"+{st.session_state.profit_cumule:.2f} USDC")
    c3.metric("🤖 Bots Actifs", len(res_open))
except:
    prix_actuel = 1.40
    res_open = {}

# 4. Formulaire (Achat 1.5 / Vente 1.9 par défaut)
with st.form("form_bot"):
    st.subheader("➕ Lancer un Bot")
    col1, col2, col3 = st.columns(3)
    p_achat = col1.number_input("Prix d'ACHAT (VERT)", value=1.5000, format="%.4f")
    p_vente = col2.number_input("Prix de VENTE (ROUGE)", value=1.9000, format="%.4f")
    vol = col3.number_input("Volume (XRP)", value=12.0)
    submit = st.form_submit_button("🚀 ACTIVER LE BOT")

if submit:
    try:
        order_data = {'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
                      'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'}
        k.query_private('AddOrder', order_data)
        st.success("✅ Bot ajouté !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# 5. TABLEAU AVEC COULEURS VISUELLES
st.write("---")
st.subheader("📦 Ma Grille de Trading")

if res_open:
    data = []
    for oid, det in res_open.items():
        t = det['descr']['type'].upper()
        data.append({
            "ID": oid[:6],
            "Type": "📥 ACHAT" if t == "BUY" else "💰 VENTE",
            "Prix": float(det['descr']['price']),
            "Quantité": float(det['vol']),
            "_color": t # Colonne cachée pour la logique
        })
    
    df = pd.DataFrame(data)

    # Fonction de style pour colorer les lignes proprement
    def style_rows(row):
        color = 'background-color: rgba(46, 204, 113, 0.3)' if row['_color'] == 'BUY' else 'background-color: rgba(231, 76, 60, 0.3)'
        return [color] * len(row)

    # Affichage du tableau (on cache la colonne de logique _color)
    st.dataframe(df.style.apply(style_rows, axis=1), use_container_width=True, column_order=("ID", "Type", "Prix", "Quantité"))
else:
    st.info("Aucun bot actif.")

# 6. BOUTON RESET (Placé en dehors, bien visible en bas)
st.write("---")
if st.button("🗑️ RESET TOTAL (Annuler tous les ordres)", use_container_width=True):
    k.query_private('CancelAll')
    st.session_state.profit_cumule = 0.0
    st.warning("Tous les ordres ont été supprimés.")
    st.rerun()
