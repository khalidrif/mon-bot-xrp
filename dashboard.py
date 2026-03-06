import streamlit as st
import krakenex

# 1. Configuration Look & Feel
st.set_page_config(page_title="XRP Cockpit", layout="wide")
st.markdown("""
    <style>
    .bot-card { border-radius: 15px; padding: 20px; margin-bottom: 20px; border: 2px solid #f0f2f6; }
    .price-label { font-size: 0.9em; color: #666; }
    .price-val { font-size: 1.2em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🕹️ Cockpit Multi-Bots XRP")

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(ticker['result']['XRPUSDC']['c'][0])
    st.metric("PRIX ACTUEL XRP", f"{prix_actuel:.4f} USDC", border=True)
    
    res_open = k.query_private('OpenOrders')
    ordres = res_open.get('result', {}).get('open', {})
except:
    st.error("Connexion Kraken impossible.")
    ordres = {}

# 4. Formulaire de Lancement (En haut, compact)
with st.expander("🚀 CONFIGURER UN NOUVEAU BOT", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    p_in = c1.number_input("PRIX ACHAT", value=1.0400, format="%.4f")
    p_out = c2.number_input("PRIX VENTE", value=1.4000, format="%.4f")
    vol = c3.number_input("QUANTITÉ", value=12.0)
    if c4.button("⚡ ACTIVER LE BOT", use_container_width=True):
        try:
            # On stocke les deux prix dans userref (Mémoire)
            memo = int(p_in * 10000) * 1000000 + int(p_out * 10000)
            k.query_private('AddOrder', {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(vol),
                'userref': str(memo),
                'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
            })
            st.rerun()
        except: st.error("Erreur")

st.write("---")

# 5. GRILLE DE BOTS (LE STYLE QUE TU CHERCHES)
if ordres:
    # On crée des colonnes (3 bots par ligne)
    cols = st.columns(3)
    for i, (oid, det) in enumerate(ordres.items()):
        with cols[i % 3]:
            type_o = det['descr']['type'].upper()
            prix_o = float(det['descr']['price'])
            
            # Récupération mémoire
            try:
                val_ref = int(det.get('userref', 0))
                p_in_memo = (val_ref // 1000000) / 10000
                p_out_memo = (val_ref % 1000000) / 10000
            except: p_in_memo, p_out_memo = 0.0, 0.0

            # Style de la carte selon l'état
            if type_o == "BUY":
                st.success(f"🟢 BOT #{i+1} : EN ATTENTE ACHAT")
                st.write(f"**ENTRÉE :** {prix_o:.4f}")
                st.write(f"**SORTIE PRÉVUE :** {p_out_memo:.4f}")
            else:
                st.error(f"🔴 BOT #{i+1} : EN ATTENTE VENTE")
                st.write(f"**ENTRÉE :** {p_in_memo:.4f} ✅")
                st.write(f"**SORTIE (CIBLE) :** {prix_o:.4f}")
            
            st.write(f"💰 **VALEUR FINALE :** {prix_o * float(det['vol']):.2f} USDC")
            
            if st.button(f"STOP BOT #{i+1}", key=oid):
                k.query_private('CancelOrder', {'txid': oid})
                st.rerun()
else:
    st.info("Aucun bot actif.")

# 6. RESET
if st.sidebar.button("🗑️ TOUT ANNULER"):
    k.query_private('CancelAll')
    st.rerun()
