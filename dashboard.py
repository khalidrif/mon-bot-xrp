import streamlit as st
import krakenex

st.set_page_config(page_title="XRP Command Center", layout="wide")
st.title("🎮 Centre de Contrôle XRP")

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# --- SÉCURITÉ ANTI-RECHARGEMENT ---
if 'dernier_ordre' not in st.session_state:
    st.session_state.dernier_ordre = None

try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    st.metric("Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    res_open = k.query_private('OpenOrders')['result']['open']
except:
    res_open = {}

with st.expander("🚀 LANCER UN NOUVEAU BOT", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    p_in = col1.number_input("ACHAT (Bas)", value=1.0400, format="%.4f")
    p_out = col2.number_input("VENTE (Haut)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité XRP", value=12.0)
    
    # Bouton avec sécurité
    if col4.button("⚡ ACTIVER"):
        # On vérifie si on vient déjà de lancer exactement le même ordre
        id_unique = f"{p_in}-{p_out}-{vol}"
        
        if st.session_state.dernier_ordre == id_unique:
            st.warning("⚠️ Ordre déjà envoyé, j'évite le doublon !")
        else:
            try:
                memo = int(p_in * 1000)
                res = k.query_private('AddOrder', {
                    'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(vol),
                    'userref': str(memo),
                    'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
                })
                # On enregistre qu'on a fini cet ordre
                st.session_state.dernier_ordre = id_unique
                st.success("✅ Ordre unique envoyé !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- AFFICHAGE DES CARTES ---
st.subheader(f"🤖 Mes Bots Actifs ({len(res_open)})")
if res_open:
    cols = st.columns(3)
    for i, (oid, det) in enumerate(res_open.items()):
        with cols[i % 3]:
            type_o = det['descr']['type'].upper()
            prix_o = float(det['descr']['price'])
            st.markdown(f"--- \n ### {'🟢' if type_o == 'BUY' else '🔴'} Bot {i+1}")
            st.write(f"**Cible :** {prix_o:.4f}")
            if st.button(f"❌ STOP BOT {i+1}", key=oid):
                k.query_private('CancelOrder', {'txid': oid})
                st.rerun()
