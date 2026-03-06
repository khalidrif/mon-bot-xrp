import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration
st.set_page_config(page_title="Kraken Multi-Bot Expert", layout="wide")
st.title("❄️ XRP Snowball : Pilotage avec Mémoire")

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'])
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
        # ASTUCE : On cache le prix de sortie dans l'identifiant pour ne jamais l'oublier
        # userref ne prend que des chiffres, on multiplie par 10000 pour garder les décimales
        ref_id = int(p_sortie * 10000) 
        
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_entree), 'volume': str(vol),
            'userref': str(ref_id),
            'close[ordertype]': 'limit', 'close[price]': str(p_sortie), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.success(f"✅ Bot lancé ! Fourchette : {p_entree} -> {p_sortie}")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# 5. TABLEAU DE BORD DÉTAILLÉ
st.write("---")
st.subheader("📋 Liste des Bots et Fourchettes")

if res_open:
    data_display = []
    for i, (oid, det) in enumerate(res_open.items(), start=1):
        type_actuel = det['descr']['type'].upper()
        prix_actuel_ordre = float(det['descr']['price'])
        vol_ordre = float(det['vol'])
        
        # On récupère le prix de sortie caché dans userref
        try:
            p_sortie_memo = int(det.get('userref', 0)) / 10000
            p_entree_memo = prix_actuel_ordre if type_actuel == "BUY" else "✅ Fait"
        except:
            p_sortie_memo = "???"
            p_entree_memo = "???"

        data_display.append({
            "Bot": f"Bot {i}",
            "État": "🟢 ATTENTE ACHAT" if type_actuel == "BUY" else "🔴 ATTENTE VENTE",
            "Prix ENTRÉE": f"{p_entree_memo}",
            "Prix SORTIE": f"{p_sortie_memo:.4f}" if isinstance(p_sortie_memo, float) else "---",
            "Montant Engagé": f"{prix_actuel_ordre * vol_ordre:.2f} USDC",
            "_style": type_actuel
        })
    
    df = pd.DataFrame(data_display)
    def style_rows(row):
        color = 'background-color: rgba(46, 204, 113, 0.15)' if row['_style'] == 'BUY' else 'background-color: rgba(231, 76, 60, 0.15)'
        return [color] * len(row)

    st.dataframe(df.style.apply(style_rows, axis=1), use_container_width=True, column_order=("Bot", "État", "Prix ENTRÉE", "Prix SORTIE", "Montant Engagé"))
else:
    st.info("Aucun bot actif.")

# 6. RESET
st.write("---")
if st.button("🗑️ RESET TOTAL", use_container_width=True):
    k.query_private('CancelAll')
    st.rerun()
