import streamlit as st
import krakenex
import pandas as pd

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
    p_in = col1.number_input("Prix ACHAT (Entrée)", value=1.0400, format="%.4f")
    p_out = col2.number_input("Prix SORTIE (Vente)", value=1.4080, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    submit = st.form_submit_button(f"🚀 LANCER LE BOT {num_prochain}")

if submit:
    try:
        # On mémorise l'ACHAT dans 'userref' (multiplié par 10000)
        memo_in = int(p_in * 10000)
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(vol),
            'userref': str(memo_in),
            'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.success(f"✅ Bot {num_prochain} lancé !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# 5. TABLEAU DE BORD (Correction Affichage Séparé)
st.write("---")
st.subheader("📋 Liste des Bots")

if res_open:
    data_display = []
    for i, (oid, det) in enumerate(res_open.items(), start=1):
        t = det['descr']['type'].upper()
        p_actuel_ordre = float(det['descr']['price'])
        
        # On récupère le prix d'entrée mémorisé dans Kraken
        try:
            val_ref = int(det.get('userref', 0))
            p_in_memo = val_ref / 10000 if val_ref > 0 else 0.0
        except:
            p_in_memo = 0.0

        # LOGIQUE D'AFFICHAGE DEMANDÉE
        if t == "BUY":
            p_entree_txt = f"{p_actuel_ordre:.4f}"
            p_sortie_txt = "---"
            etat = "🟢 ATTENTE ACHAT"
        else:
            # Si c'est une vente, on montre le prix d'achat avec sa COCHE
            p_entree_txt = f"{p_in_memo:.4f} ✅" if p_in_memo > 0 else "--- ✅"
            p_sortie_txt = f"{p_actuel_ordre:.4f}"
            etat = "🔴 ATTENTE VENTE"

        data_display.append({
            "Bot": f"Bot {i}",
            "État": etat,
            "Prix ENTRÉE": p_entree_txt,
            "Prix SORTIE": p_sortie_txt,
            "Valeur Totale": f"{p_actuel_ordre * float(det['vol']):.2f} USDC",
            "_style": t
        })
    
    df = pd.DataFrame(data_display)

    def style_rows(row):
        color = 'background-color: rgba(46, 204, 113, 0.15)' if row['_style'] == 'BUY' else 'background-color: rgba(231, 76, 60, 0.15)'
        return [color] * len(row)

    st.dataframe(
        df.style.apply(style_rows, axis=1),
        use_container_width=True,
        column_order=("Bot", "État", "Prix ENTRÉE", "Prix SORTIE", "Valeur Totale")
    )
else:
    st.info("Aucun bot actif.")

# 6. RESET
st.write("---")
if st.button("🗑️ RESET TOTAL", use_container_width=True):
    k.query_private('CancelAll')
    st.rerun()
