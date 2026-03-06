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
    p_entree = col1.number_input("Prix ACHAT (Entrée)", value=1.0400, format="%.4f")
    p_sortie = col2.number_input("Prix SORTIE (Vente)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    submit = st.form_submit_button(f"🚀 LANCER LE BOT {num_prochain}")

if submit:
    try:
        # On utilise 'userref' pour stocker le prix d'achat initial (format entier pour Kraken)
        memo_prix = int(p_entree * 10000)
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_entree), 'volume': str(vol),
            'userref': str(memo_prix),
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
    for i, (oid, det) in enumerate(res_open.items(), start=1):
        t = det['descr']['type'].upper()
        prix_actuel_ordre = float(det['descr']['price'])
        vol_ordre = float(det['vol'])
        
        # On récupère le prix d'achat mémorisé dans userref
        try:
            p_achat_memo = int(det.get('userref', 0)) / 10000
        except:
            p_achat_memo = 0.0

        # Logique d'affichage demandée
        if t == "BUY":
            etat = "🟢 ATTENTE ACHAT"
            p_in_display = f"{prix_actuel_ordre:.4f}"
            p_out_display = "---"
            montant = prix_actuel_ordre * vol_ordre
        else:
            etat = "🔴 ATTENTE VENTE"
            # On affiche le prix d'achat mémorisé avec la coche
            p_in_display = f"{p_achat_memo:.4f} ✅" if p_achat_memo > 0 else "✅ FAIT"
            p_out_display = f"{prix_actuel_ordre:.4f}"
            montant = prix_actuel_ordre * vol_ordre

        data_display.append({
            "ID": f"Bot {i}",
            "État": etat,
            "Prix Entrée": p_in_display,
            "Prix Sortie": p_out_display,
            "Montant + Profit": f"{montant:.2f} USDC",
            "_style": t
        })
    
    df = pd.DataFrame(data_display)

    def color_rows(row):
        color = 'background-color: rgba(46, 204, 113, 0.15)' if row['_style'] == 'BUY' else 'background-color: rgba(231, 76, 60, 0.15)'
        return [color] * len(row)

    st.dataframe(
        df.style.apply(color_rows, axis=1),
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
