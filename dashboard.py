import streamlit as st
import krakenex

# 1. Configuration Look & Feel
st.set_page_config(page_title="XRP Cockpit", layout="wide")

# Style pour les cartes
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; }
    .stMetric { border: 1px solid #ddd; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- MENU GAUCHE (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Réglages")
    st.write("Zone de sécurité")
    if st.button("🗑️ TOUT ANNULER", type="primary", use_container_width=True):
        k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])
        k.query_private('CancelAll')
        st.rerun()

st.title("🕹️ Cockpit Multi-Bots XRP")

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(ticker['result']['XRPUSDC']['c'][0])
    st.metric("PRIX ACTUEL XRP", f"{prix_actuel:.4f} USDC")
    
    res_open = k.query_private('OpenOrders')
    ordres = res_open.get('result', {}).get('open', {})
except:
    st.error("Connexion Kraken impossible.")
    ordres = {}

# 4. Formulaire de Lancement (Compact)
with st.expander("🚀 CONFIGURER UN NOUVEAU BOT", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    p_in = c1.number_input("PRIX ACHAT", value=1.0400, format="%.4f")
    p_out = c2.number_input("PRIX VENTE", value=1.4000, format="%.4f")
    vol = c3.number_input("QUANTITÉ", value=12.0)
    if c4.button("⚡ ACTIVER LE BOT"):
        try:
            # Mémoire des prix dans userref
            memo = int(p_in * 10000) * 1000000 + int(p_out * 10000)
            k.query_private('AddOrder', {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(vol),
                'userref': str(memo),
                'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
            })
            st.rerun()
        except: st.error("Erreur de lancement")

st.write("---")

# 5. GRILLE DE BOTS (Style Cartes)
if ordres:
    st.subheader(f"🤖 Bots Actifs ({len(ordres)})")
    cols = st.columns(3) # 3 bots par ligne
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

            # Design selon l'état
            if type_o == "BUY":
                st.success(f"🟢 BOT #{i+1} : ACHAT EN COURS")
                st.write(f"**Cible Achat :** {prix_o:.4f}")
                st.write(f"**Vente prévue :** {p_out_memo:.4f}")
            else:
                st.error(f"🔴 BOT #{i+1} : VENTE EN COURS")
                st.write(f"**Acheté à :** {p_in_memo:.4f} ✅")
                st.write(f"**Cible Vente :** {prix_o:.4f}")
            
            st.write(f"💰 **Valeur finale :** {prix_o * float(det['vol']):.2f} USDC")
            
            if st.button(f"STOP BOT #{i+1}", key=oid):
                k.query_private('CancelOrder', {'txid': oid})
                st.rerun()
else:
    st.info("Aucun bot actif.")
