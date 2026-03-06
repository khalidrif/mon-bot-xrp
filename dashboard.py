import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration
st.set_page_config(page_title="Kraken Multi-Bot Expert", layout="wide")
st.title("❄️ XRP Snowball : Pilotage en Direct")

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
    # Compteur pour l'ID visuel
    for i, (oid, det) in enumerate(res_open.items(), start=1):
        type_actuel = det['descr']['type'].upper()
        prix_ordre = float(det['descr']['price'])
        vol_ordre = float(det['vol'])
        
        # Affichage propre sans pointillés
        # Si c'est un achat (Vert), on remplit la colonne Entrée
        # Si c'est une vente (Rouge), on remplit la colonne Sortie
        p_in = f"{prix_ordre:.4f}" if type_actuel == "BUY" else "Effectué ✅"
        p_out = f"{prix_ordre:.4f}" if type_actuel == "SELL" else "En attente..."

        data_display.append({
            "ID": f"Bot {i}",
            "État": "🟢 ATTENTE ACHAT" if type_actuel == "BUY" else "🔴 ATTENTE VENTE",
            "Prix Entrée": p_in,
            "Prix Sortie": p_out,
            "Montant + Profit": f"{prix_ordre * vol_ordre:.2f} USDC",
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
