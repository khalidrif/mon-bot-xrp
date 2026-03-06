import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="XRP Snowball Tracker", layout="wide")
st.title("❄️ Console XRP : Suivi des Bots Individuels")

# Initialisation du profit session
if 'profit_session' not in st.session_state:
    st.session_state.profit_session = 0.0

# 2. Connexion Kraken
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Temps Réel
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    res_open = k.query_private('OpenOrders')['result']['open']
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    c2.metric("💰 Profit Cumulé", f"+{st.session_state.profit_session:.2f} USDC")
    c3.metric("🤖 Bots en cours", len(res_open))
except:
    st.error("Connexion Kraken impossible.")
    res_open = {}

# 4. Formulaire de lancement (Exemple 1.04 - 1.5)
with st.form("form_bot"):
    st.subheader("➕ Configurer un nouveau Bot")
    col1, col2, col3 = st.columns(3)
    p_achat = col1.number_input("Prix ACHAT (Vert)", value=1.0400, format="%.4f")
    p_vente = col2.number_input("Prix VENTE (Rouge)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    
    # Calcul profit pour affichage info
    gain_net = (p_vente - p_achat) * vol
    st.info(f"💡 Ce bot rapportera **{gain_net:.2f} USDC** de profit net.")
    
    submit = st.form_submit_button("🚀 LANCER LE BOT")

if submit:
    try:
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
            'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.session_state.profit_session += gain_net
        st.success(f"✅ Bot programmé avec succès !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# 5. TABLEAU DE BORD (Liste des Bots)
st.write("---")
st.subheader("📋 État des Bots")

if res_open:
    data_display = []
    for oid, det in res_open.items():
        type_actuel = det['descr']['type'].upper()
        prix_cible = float(det['descr']['price'])
        quantite = float(det['vol'])
        total_usdc = prix_cible * quantite # Montant que tu récupères à ce palier
        
        # Logique d'affichage demandée
        etat = "🟢 Attente ACHAT" if type_actuel == "BUY" else "🔴 Attente VENTE"
        couleur_ligne = "buy" if type_actuel == "BUY" else "sell"

        data_display.append({
            "Bot ID": oid[:6],
            "État du Bot": etat,
            "Prix Cible": f"{prix_cible:.4f} USDC",
            "Quantité": f"{quantite} XRP",
            "Valeur Totale": f"{total_usdc:.2f} USDC",
            "_style": couleur_ligne
        })
    
    df = pd.DataFrame(data_display)

    # Fonction de style pour les couleurs Vert/Rouge
    def apply_color(row):
        color = 'background-color: rgba(46, 204, 113, 0.2)' if row['_style'] == 'buy' else 'background-color: rgba(231, 76, 60, 0.2)'
        return [color] * len(row)

    # Affichage du tableau stylisé
    st.dataframe(
        df.style.apply(apply_color, axis=1), 
        use_container_width=True, 
        column_order=("Bot ID", "État du Bot", "Prix Cible", "Quantité", "Valeur Totale")
    )
else:
    st.info("Aucun bot actif pour le moment.")

# 6. BOUTON RESET (En dehors du tableau)
st.write("---")
if st.button("🗑️ RESET TOTAL (Annuler tous les ordres)", use_container_width=True):
    k.query_private('CancelAll')
    st.session_state.profit_session = 0.0
    st.rerun()
