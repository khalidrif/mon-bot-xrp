import streamlit as st
import krakenex
import pandas as pd
import re

# 1. Configuration
st.set_page_config(page_title="Kraken Multi-Bot Expert", layout="wide")
st.title("❄️ XRP Snowball : Console de Pilotage")

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
    num_prochain = len(res_open) + 1
    st.subheader(f"➕ Configurer le Bot {num_prochain}")
    
    col1, col2, col3 = st.columns(3)
    p_entree = col1.number_input("Prix ENTRÉE (Achat)", value=1.0400, format="%.4f")
    p_sortie = col2.number_input("Prix SORTIE (Vente)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    
    submit = st.form_submit_button(f"🚀 LANCER LE BOT {num_prochain}")

if submit:
    try:
        # On stocke le prix de sortie dans 'userref' pour le retrouver plus tard (format simple)
        # On utilise un identifiant unique basé sur le temps pour ne pas mélanger
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_entree), 'volume': str(vol),
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
    index_bot = 1
    for oid, det in res_open.items():
        type_actuel = det['descr']['type'].upper()
        prix_ordre = float(det['descr']['price'])
        vol_ordre = float(det['vol'])
        
        # Extraction des prix depuis la description de l'ordre (order info)
        # Kraken affiche souvent "buy... @ limit 1.0400" ou "sell... @ limit 1.5000"
        desc = det['descr']['order']
        prix_dans_desc = re.findall(r"\d+\.\d+", desc)
        
        # Si on est en achat, le prix d'entrée est le prix de l'ordre actuel
        # Pour le prix de sortie, on regarde si un ordre 'close' est lié (if done)
        p_in = prix_ordre if type_actuel == "BUY" else "---" 
        p_out = prix_ordre if type_actuel == "SELL" else "---"

        # Note: Kraken ne renvoie pas le prix "if-done" facilement dans OpenOrders simple
        # On va donc afficher le prix de l'étape ACTUELLE de manière très claire
        data_display.append({
            "ID": f"Bot {index_bot}",
            "État": "🟢 ATTENTE ACHAT" if type_actuel == "BUY" else "🔴 ATTENTE VENTE",
            "Prix Entrée": f"{p_in}",
            "Prix Sortie": f"{p_out}",
            "Montant + Profit": f"{prix_ordre * vol_ordre:.2f} USDC",
            "_style": type_actuel
        })
        index_bot += 1
    
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
