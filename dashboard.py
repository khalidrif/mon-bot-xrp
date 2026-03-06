import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="Kraken Multi-Bot Recovery", layout="wide")
st.title("❄️ XRP Snowball : Console de Pilotage")

# 2. Connexion sécurisée
try:
    k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])
except:
    st.error("🔑 Erreur : Vérifie tes Secrets (KRAKEN_KEY / KRAKEN_SECRET) !")

# 3. Récupération des données Marché
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    
    res_open = k.query_private('OpenOrders')['result']['open']
    
    c1, c2 = st.columns(2)
    c1.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    c2.metric("🤖 Bots Actifs chez Kraken", len(res_open))
except Exception as e:
    st.warning(f"⚠️ En attente de connexion ou Kraken indisponible : {e}")
    prix_actuel = 1.40
    res_open = {}

# 4. Formulaire de lancement (Configuration Bot 1.04 - 1.50)
with st.form("form_bot"):
    num_prochain = len(res_open) + 1
    st.subheader(f"➕ Lancer le Bot {num_prochain}")
    col1, col2, col3 = st.columns(3)
    p_in = col1.number_input("ACHAT (Entrée)", value=1.0400, format="%.4f")
    p_out = col2.number_input("VENTE (Sortie)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    submit = st.form_submit_button(f"🚀 ACTIVER LE BOT {num_prochain}")

if submit:
    try:
        # On enregistre le prix de sortie dans 'userref' pour ne jamais le perdre (format simplifié)
        ref_p_out = int(p_out * 1000)
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(vol),
            'userref': str(ref_p_out),
            'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.success(f"✅ Bot {num_prochain} lancé !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur Kraken : {e}")

# 5. TABLEAU DE BORD (Détails des Bots)
st.write("---")
st.subheader("📋 État de tes Bots")

if res_open:
    data_display = []
    for i, (oid, det) in enumerate(res_open.items(), start=1):
        t = det['descr']['type'].upper()
        p_actuel_ordre = float(det['descr']['price'])
        v_ordre = float(det['vol'])
        
        # On tente de retrouver le prix de sortie via le userref enregistré
        try:
            val_ref = int(det.get('userref', 0))
            p_sortie_memo = val_ref / 1000 if val_ref > 0 else p_out # p_out par défaut
        except:
            p_sortie_memo = "---"

        data_display.append({
            "Bot": f"Bot {i}",
            "État": "🟢 ATTENTE ACHAT" if t == "BUY" else "🔴 ATTENTE VENTE",
            "Prix Entrée": f"{p_actuel_ordre:.4f}" if t == "BUY" else "✅ FAIT",
            "Prix Sortie": f"{p_sortie_memo:.4f}" if t == "BUY" else f"{p_actuel_ordre:.4f}",
            "Montant + Profit": f"{p_actuel_ordre * v_ordre:.2f} USDC",
            "_style": t
        })
    
    df = pd.DataFrame(data_display)

    def style_rows(row):
        color = 'background-color: rgba(46, 204, 113, 0.15)' if row['_style'] == 'BUY' else 'background-color: rgba(231, 76, 60, 0.15)'
        return [color] * len(row)

    st.dataframe(
        df.style.apply(style_rows, axis=1),
        use_container_width=True,
        column_order=("Bot", "État", "Prix Entrée", "Prix Sortie", "Montant + Profit")
    )
else:
    st.info("Aucun bot actif. Ton argent est en sécurité dans ton solde Kraken.")

# 6. RESET TOTAL (Placé en bas de page)
st.write("---")
if st.button("🗑️ RESET TOTAL (Tout effacer)", use_container_width=True):
    k.query_private('CancelAll')
    st.rerun()
