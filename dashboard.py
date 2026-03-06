import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration
st.set_page_config(page_title="Kraken Multi-Bot Expert", layout="wide")
st.title("❄️ XRP Snowball : Console Simplifiée")

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    res_open = k.query_private('OpenOrders')['result']['open']
    
    st.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
except:
    st.error("Connexion Kraken impossible.")
    res_open = {}

# 4. Formulaire
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
        # On mémorise le prix d'achat initial dans 'userref' pour ne jamais le perdre
        memo_prix = int(p_achat * 10000)
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
            'userref': str(memo_prix),
            'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.success(f"✅ Bot {num_prochain} lancé !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# 5. TABLEAU SIMPLIFIÉ (Compréhensible immédiatement)
st.write("---")
st.subheader("📋 Liste des Bots")

if res_open:
    data_display = []
    for i, (oid, det) in enumerate(res_open.items(), start=1):
        type_actuel = det['descr']['type'].upper()
        prix_ordre = float(det['descr']['price'])
        
        # On essaie de retrouver le prix d'achat mémorisé
        try:
            p_achat_initial = int(det.get('userref', 0)) / 10000
        except:
            p_achat_initial = 0.0

        # Logique d'affichage ULTRA CLAIRE
        if type_actuel == "BUY":
            # Phase : On attend d'acheter
            etat = "🟢 Attente ACHAT"
            p_achat_visuel = f"{prix_ordre:.4f}"
            p_vente_visuel = "---" # On ne connaît pas encore la vente dans ce mode
            couleur = "buy"
        else:
            # Phase : On a acheté, on attend de vendre
            etat = "🔴 Attente VENTE"
            p_achat_visuel = f"{p_achat_initial:.4f} ✅" if p_achat_initial > 0 else "--- ✅"
            p_vente_visuel = f"{prix_ordre:.4f}"
            couleur = "sell"

        data_display.append({
            "BOT": f"Bot {i}",
            "PRIX ACHAT": p_achat_visuel,
            "PRIX VENTE": p_vente_visuel,
            "ÉTAT": etat,
            "MONTANT + PROFIT": f"{prix_ordre * float(det['vol']):.2f} USDC",
            "_style": couleur
        })
    
    df = pd.DataFrame(data_display)

    def style_rows(row):
        color = 'background-color: rgba(46, 204, 113, 0.2)' if row['_style'] == 'buy' else 'background-color: rgba(231, 76, 60, 0.2)'
        return [color] * len(row)

    st.dataframe(
        df.style.apply(style_rows, axis=1),
        use_container_width=True,
        column_order=("BOT", "PRIX ACHAT", "PRIX VENTE", "ÉTAT", "MONTANT + PROFIT")
    )
else:
    st.info("Aucun bot actif.")

# 6. RESET
st.write("---")
if st.button("🗑️ RESET TOTAL", use_container_width=True):
    k.query_private('CancelAll')
    st.rerun()
