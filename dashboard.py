import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration
st.set_page_config(page_title="Kraken Multi-Bot Expert", layout="wide")
st.title("❄️ XRP Snowball : Console de Pilotage")

# Initialisation du compteur si vide
if 'nb_bots' not in st.session_state:
    st.session_state.nb_bots = 0

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    res_open = k.query_private('OpenOrders')['result']['open']
    
    c1, c2 = st.columns(2)
    c1.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    c2.metric("🤖 Bots Actifs", len(res_open))
except:
    st.error("Connexion Kraken impossible.")
    res_open = {}

# 4. Formulaire
with st.form("form_bot"):
    # On calcule le numéro du prochain bot basé sur ceux déjà ouverts + 1
    num_prochain = len(res_open) + 1
    st.subheader(f"➕ Configurer le Bot {num_prochain}")
    
    col1, col2, col3 = st.columns(3)
    p_entree = col1.number_input("Prix ENTRÉE (Vert)", value=1.0400, format="%.4f")
    p_sortie = col2.number_input("Prix SORTIE (Rouge)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    
    submit = st.form_submit_button(f"🚀 LANCER LE BOT {num_prochain}")

if submit:
    try:
        # On envoie l'ID du bot dans 'userref' pour qu'il soit sauvegardé chez Kraken
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_entree), 'volume': str(vol),
            'userref': str(num_prochain),
            'close[ordertype]': 'limit', 'close[price]': str(p_sortie), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.success(f"✅ Bot {num_prochain} lancé !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# 5. TABLEAU DE BORD
st.write("---")
st.subheader("📋 Liste des Bots Actifs")

if res_open:
    data_display = []
    # On trie les ordres pour que Bot 1 soit en haut
    for oid, det in res_open.items():
        type_actuel = det['descr']['type'].upper()
        # On récupère le numéro du bot stocké dans userref (ou on met ? si vide)
        id_bot = det.get('userref', '0')
        
        # On extrait les prix de la description Kraken (ex: "buy 12.0 XRPUSDC @ limit 1.0400")
        desc = det['descr']['order']
        # Si c'est un achat, le prix actuel est l'entrée. Si c'est une vente, c'est la sortie.
        prix_actuel_ordre = float(det['descr']['price'])
        
        data_display.append({
            "ID": f"Bot {id_bot}",
            "État": "🟢 ATTENTE ACHAT" if type_actuel == "BUY" else "🔴 ATTENTE VENTE",
            "Prix Entrée": f"{prix_actuel_ordre:.4f}" if type_actuel == "BUY" else "---",
            "Prix Sortie": f"{prix_actuel_ordre:.4f}" if type_actuel == "SELL" else "---",
            "Montant + Profit": f"{prix_actuel_ordre * float(det['vol']):.2f} USDC",
            "_style": type_actuel
        })
    
    df = pd.DataFrame(data_display)

    def style_rows(row):
        color = 'background-color: rgba(46, 204, 113, 0.2)' if row['_style'] == 'BUY' else 'background-color: rgba(231, 76, 60, 0.2)'
        return [color] * len(row)

    st.dataframe(
        df.style.apply(style_rows, axis=1),
        use_container_width=True,
        column_order=("ID", "État", "Prix Entrée", "Prix Sortie", "Montant + Profit")
    )
else:
    st.info("Aucun bot actif.")

# 6. RESET
st.write("---")
if st.button("🗑️ RESET TOTAL", use_container_width=True):
    k.query_private('CancelAll')
    st.rerun()
