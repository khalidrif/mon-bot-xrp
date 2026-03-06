import streamlit as st
import krakenex
import pandas as pd
import re

# 1. Configuration
st.set_page_config(page_title="Kraken Multi-Bot Tracker", layout="wide")
st.title("❄️ XRP Snowball : Console de Pilotage")

if 'profit_session' not in st.session_state:
    st.session_state.profit_session = 0.0
if 'nb_bots_lances' not in st.session_state:
    st.session_state.nb_bots_lances = 0

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    res_open = k.query_private('OpenOrders')['result']['open']
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    c2.metric("💰 Profit Session", f"+{st.session_state.profit_session:.2f} USDC")
    c3.metric("🤖 Bots Actifs", len(res_open))
except:
    st.error("Connexion Kraken impossible.")
    res_open = {}

# 4. Formulaire
with st.form("form_bot"):
    id_suivant = st.session_state.nb_bots_lances + 1
    st.subheader(f"➕ Configurer le Bot {id_suivant}")
    col1, col2, col3 = st.columns(3)
    p_entree = col1.number_input("Prix ENTRÉE (Achat)", value=1.0400, format="%.4f")
    p_sortie = col2.number_input("Prix SORTIE (Vente)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    submit = st.form_submit_button(f"🚀 LANCER LE BOT {id_suivant}")

if submit:
    try:
        st.session_state.nb_bots_lances += 1
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_entree), 'volume': str(vol),
            'userref': str(st.session_state.nb_bots_lances),
            'close[ordertype]': 'limit', 'close[price]': str(p_sortie), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.session_state.profit_session += (p_sortie - p_entree) * vol
        st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# 5. TABLEAU DE BORD
st.write("---")
if res_open:
    data_display = []
    for oid, det in res_open.items():
        type_actuel = det['descr']['type'].upper()
        prix_actuel_ordre = float(det['descr']['price'])
        
        # Extraction intelligente des prix d'entrée/sortie depuis la description Kraken
        # Kraken écrit souvent : "buy 12.0 XRPUSDC @ limit 1.0400"
        desc = det['descr']['order']
        prix_detecte = re.findall(r"\d+\.\d+", desc)
        
        # Par défaut on affiche ce qu'on trouve
        p_entree_tab = prix_detecte[1] if type_actuel == "BUY" else "---"
        p_sortie_tab = prix_detecte[1] if type_actuel == "SELL" else "---"

        data_display.append({
            "ID": f"Bot {det.get('userref', '?')}",
            "État": "🟢 ATTENTE ACHAT" if type_actuel == "BUY" else "🔴 ATTENTE VENTE",
            "Prix Entrée": f"{p_entree_tab}",
            "Prix Sortie": f"{p_sortie_tab}",
            "Cible Actuelle": f"{prix_actuel_ordre:.4f} USDC",
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

# 6. RESET
st.write("---")
if st.button("🗑️ RESET TOTAL", use_container_width=True):
    k.query_private('CancelAll')
    st.session_state.nb_bots_lances = 0
    st.rerun()
