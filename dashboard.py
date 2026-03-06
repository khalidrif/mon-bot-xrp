import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration
st.set_page_config(page_title="Kraken Multi-Bot Expert", layout="wide")
st.title("❄️ XRP Snowball : Pilotage Individuel")

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'])
    res_open = k.query_private('OpenOrders')['result']['open']
    st.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
except:
    st.error("Connexion Kraken impossible.")
    res_open = {}

# 4. Formulaire de lancement
with st.form("form_bot"):
    num_prochain = len(res_open) + 1
    st.subheader(f"➕ Configurer le Bot {num_prochain}")
    col1, col2, col3 = st.columns(3)
    p_achat = col1.number_input("Prix ACHAT (Entrée)", value=1.0400, format="%.4f")
    p_vente = col2.number_input("Prix VENTE (Sortie)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    submit = st.form_submit_button(f"🚀 LANCER LE BOT {num_prochain}")

if submit:
    try:
        memo_prix = int(p_achat * 10000)
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
            'userref': str(memo_prix),
            'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.success(f"✅ Bot lancé !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# 5. TABLEAU DE BORD
st.write("---")
st.subheader("📋 Liste des Bots Actifs")

dict_annuler = {} # Pour stocker les IDs de chaque bot

if res_open:
    data_display = []
    for i, (oid, det) in enumerate(res_open.items(), start=1):
        t = det['descr']['type'].upper()
        p_ordre = float(det['descr']['price'])
        nom_visuel = f"Bot {i}"
        dict_annuler[nom_visuel] = oid # On lie le nom à l'ID Kraken
        
        try:
            p_achat_init = int(det.get('userref', 0)) / 10000
        except:
            p_achat_init = 0.0

        if t == "BUY":
            p_achat_txt, p_vente_txt, etat, coul = f"{p_ordre:.4f}", "---", "🟢 ACHAT", "buy"
        else:
            p_achat_txt, p_vente_txt, etat, coul = f"{p_achat_init:.4f} ✅", f"{p_ordre:.4f}", "🔴 VENTE", "sell"

        data_display.append({"BOT": nom_visuel, "ACHAT": p_achat_txt, "VENTE": p_vente_txt, "ÉTAT": etat, "VALEUR": f"{p_ordre * float(det['vol']):.2f} USDC", "_style": coul})
    
    df = pd.DataFrame(data_display)
    st.dataframe(df.style.apply(lambda r: ['background-color: rgba(46, 204, 113, 0.2)' if r['_style'] == 'buy' else 'background-color: rgba(231, 76, 60, 0.2)'] * len(r), axis=1), use_container_width=True, column_order=("BOT", "ACHAT", "VENTE", "ÉTAT", "VALEUR"))

    # --- NOUVEAU : ANNULATION INDIVIDUELLE ---
    st.write("### 🛠️ Gestion Individuelle")
    col_del, col_btn = st.columns([2, 1])
    bot_a_supprimer = col_del.selectbox("Choisir un bot à arrêter :", options=list(dict_annuler.keys()))
    
    if col_btn.button("🗑️ SUPPRIMER CE BOT"):
        id_kraken = dict_annuler[bot_a_supprimer]
        k.query_private('CancelOrder', {'txid': id_kraken})
        st.warning(f"{bot_a_supprimer} annulé.")
        st.rerun()
else:
    st.info("Aucun bot actif.")

# 6. RESET TOTAL
st.write("---")
if st.sidebar.button("⚠️ RESET TOTAL"):
    k.query_private('CancelAll')
    st.rerun()
