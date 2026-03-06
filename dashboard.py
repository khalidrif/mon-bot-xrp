import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration
st.set_page_config(page_title="Kraken Snowball Expert", layout="wide")
st.title("❄️ XRP Snowball : Prix + Coche ✅")

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
    p_out = col2.number_input("Prix SORTIE (Vente)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    submit = st.form_submit_button(f"🚀 LANCER LE BOT {num_prochain}")

if submit:
    try:
        # On mémorise le prix d'entrée dans userref (multiplié par 10000)
        memo_prix = int(p_in * 10000)
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(vol),
            'userref': str(memo_prix),
            'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.success("✅ Bot lancé !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")

# 5. TABLEAU DE BORD (Correction Prix + Coche)
st.write("---")
st.subheader("📋 État de tes Bots")

if res_open:
    data_display = []
    for i, (oid, det) in enumerate(res_open.items(), start=1):
        t = det['descr']['type'].upper()
        p_actuel_ordre = float(det['descr']['price'])
        v_ordre = float(det['vol'])
        
        # Récupération du prix d'entrée mémorisé dans Kraken
        try:
            p_in_memo = int(det.get('userref', 0)) / 10000
        except:
            p_in_memo = 0.0

        if t == "BUY":
            etat = "🟢 ATTENTE ACHAT"
            # On affiche le prix d'achat prévu
            p_in_txt = f"{p_actuel_ordre:.4f}"
            p_out_txt = "---"
        else:
            etat = "🔴 ATTENTE VENTE"
            # ICI LA CORRECTION : On affiche le prix d'achat mémorisé + la COCHE ✅
            p_in_txt = f"{p_in_memo:.4f} ✅" if p_in_memo > 0 else "--- ✅"
            p_out_txt = f"{p_actuel_ordre:.4f}"

        data_display.append({
            "Bot": f"Bot {i}",
            "État": etat,
            "Prix Entrée": p_in_txt,
            "Prix Sortie": p_out_txt,
            "Valeur du Bot": f"{p_actuel_ordre * v_ordre:.2f} USDC",
            "_style": t
        })
    
    df = pd.DataFrame(data_display)

    def style_rows(row):
        color = 'background-color: rgba(46, 204, 113, 0.15)' if row['_style'] == 'BUY' else 'background-color: rgba(231, 76, 60, 0.15)'
        return [color] * len(row)

    st.dataframe(
        df.style.apply(style_rows, axis=1),
        use_container_width=True,
        column_order=("Bot", "État", "Prix Entrée", "Prix Sortie", "Valeur du Bot")
    )
else:
    st.info("Aucun bot actif.")

# 6. RESET
st.write("---")
if st.button("🗑️ RESET TOTAL", use_container_width=True):
    k.query_private('CancelAll')
    st.rerun()
