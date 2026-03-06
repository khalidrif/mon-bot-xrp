import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="Kraken Multi-Bot Expert", layout="wide")
st.title("❄️ XRP Snowball : Console de Pilotage Experte")

# Initialisation des compteurs en mémoire
if 'profit_session' not in st.session_state:
    st.session_state.profit_session = 0.0
if 'nb_bots_lances' not in st.session_state:
    st.session_state.nb_bots_lances = 0

# 2. Connexion Kraken
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    res_open = k.query_private('OpenOrders')['result']['open']
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    c2.metric("💰 Profit Cumulé", f"+{st.session_state.profit_session:.2f} USDC")
    c3.metric("🤖 Bots Actifs", len(res_open))
except:
    st.error("Connexion Kraken impossible.")
    prix_actuel = 1.40
    res_open = {}

# 4. FORMULAIRE DE CONFIGURATION
st.write("---")
with st.form("form_bot"):
    prochain_id = st.session_state.nb_bots_lances + 1
    st.subheader(f"➕ Configurer le Bot {prochain_id}")
    col1, col2, col3 = st.columns(3)
    
    p_achat = col1.number_input("PRIX ENTRÉE (Achat)", value=1.0400, format="%.4f")
    p_vente = col2.number_input("PRIX SORTIE (Vente)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    
    profit_net = (p_vente - p_achat) * vol
    submit = st.form_submit_button(f"🚀 LANCER LE BOT {prochain_id}")

if submit:
    try:
        st.session_state.nb_bots_lances += 1
        # On utilise 'userref' pour marquer l'ID du bot chez Kraken
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
            'userref': str(st.session_state.nb_bots_lances),
            'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.session_state.profit_session += profit_net
        st.success(f"✅ Bot {st.session_state.nb_bots_lances} lancé !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur Kraken : {e}")

# 5. TABLEAU DE BORD DÉTAILLÉ
st.write("---")
st.subheader("📋 Liste des Bots et Fourchettes")

if res_open:
    data_display = []
    for i, (oid, det) in enumerate(res_open.items()):
        type_actuel = det['descr']['type'].upper()
        prix_actuel_ordre = float(det['descr']['price'])
        quantite = float(det['vol'])
        
        # Identification du Bot
        num_bot = det.get('userref', i + 1)
        id_visuel = f"Bot {num_bot}"
        
        # État et Valeur
        etat = "🟢 ATTENTE ACHAT" if type_actuel == "BUY" else "🔴 ATTENTE VENTE"
        valeur_totale = prix_actuel_ordre * quantite

        data_display.append({
            "ID": id_visuel,
            "État": etat,
            "Prix Entrée": f"{p_achat:.4f}", # Basé sur le dernier saisi pour l'affichage
            "Prix Sortie": f"{p_vente:.4f}", # Basé sur le dernier saisi pour l'affichage
            "Cible Actuelle": f"{prix_actuel_ordre:.4f} USDC",
            "Montant + Profit": f"{valeur_totale:.2f} USDC",
            "_style": type_actuel
        })
    
    df = pd.DataFrame(data_display)

    def style_rows(row):
        color = 'background-color: rgba(46, 204, 113, 0.2)' if row['_style'] == 'BUY' else 'background-color: rgba(231, 76, 60, 0.2)'
        return [color] * len(row)

    st.dataframe(
        df.style.apply(style_rows, axis=1),
        use_container_width=True,
        column_order=("ID", "État", "Prix Entrée", "Prix Sortie", "Cible Actuelle", "Montant + Profit")
    )
else:
    st.info("Aucun bot actif.")

# 6. RESET TOTAL
st.write("---")
if st.button("🗑️ RESET TOTAL (Tout annuler)", use_container_width=True):
    k.query_private('CancelAll')
    st.session_state.profit_session = 0.0
    st.session_state.nb_bots_lances = 0
    st.rerun()
