import streamlit as st
import krakenex

# 1. Configuration
st.set_page_config(page_title="XRP Line Tracker", layout="wide")
st.title("🛡️ Console de Trading XRP")

# Sécurité anti-doublon
if 'dernier_ordre' not in st.session_state:
    st.session_state.dernier_ordre = None

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(ticker['result']['XRPUSDC']['c'][0])
    st.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    
    res_open = k.query_private('OpenOrders')
    ordres_ouverts = res_open.get('result', {}).get('open', {})
except:
    st.error("Connexion Kraken impossible (Maintenance ?)")
    ordres_ouverts = {}

# 4. Zone de Lancement
with st.form("form_lancement"):
    st.write("### ➕ LANCER UN NOUVEAU BOT")
    c1, c2, c3 = st.columns(3)
    p_in = c1.number_input("ACHAT (Entrée)", value=1.0400, format="%.4f")
    p_out = c2.number_input("VENTE (Sortie)", value=1.4000, format="%.4f")
    vol = c3.number_input("Quantité XRP", value=12.0)
    submit = st.form_submit_button("🚀 ACTIVER LE BOT")

if submit:
    id_tentative = f"{p_in}-{p_out}-{vol}"
    if st.session_state.dernier_ordre == id_tentative:
        st.warning("⚠️ Déjà envoyé !")
    else:
        try:
            # Mémoire : on stocke le prix d'entrée (p_in) et de sortie (p_out) dans userref
            # Format : [ENTREE en entiers][SORTIE en entiers] -> ex: 1040014000
            memo = int(p_in * 10000) * 1000000 + int(p_out * 10000)
            k.query_private('AddOrder', {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(vol),
                'userref': str(memo),
                'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
            })
            st.session_state.dernier_ordre = id_tentative
            st.rerun()
        except: st.error("Erreur Kraken")

st.write("---")

# 5. AFFICHAGE PAR LIGNES
st.subheader(f"🤖 Mes Bots Actifs ({len(ordres_ouverts)})")

if ordres_ouverts:
    # En-tête
    h1, h2, h3, h4, h5, h6 = st.columns([1, 2, 2, 2, 2, 1])
    h1.write("**Bot**")
    h2.write("**PRIX ENTRÉE**")
    h3.write("**PRIX SORTIE**")
    h4.write("**ÉTAT**")
    h5.write("**VALEUR + PROFIT**")
    h6.write("**STOP**")

    for i, (oid, det) in enumerate(ordres_ouverts.items(), start=1):
        type_o = det['descr']['type'].upper()
        prix_o = float(det['descr']['price'])
        vol_o = float(det['vol'])
        
        # Décryptage du prix mémorisé (userref)
        try:
            val_ref = int(det.get('userref', 0))
            p_in_memo = (val_ref // 1000000) / 10000
            p_out_memo = (val_ref % 1000000) / 10000
        except: 
            p_in_memo, p_out_memo = 0.0, 0.0

        l1, l2, l3, l4, l5, l6 = st.columns([1, 2, 2, 2, 2, 1])
        
        l1.write(f"#{i}")
        
        # Logique d'affichage par ligne
        if type_o == "BUY":
            l2.write(f"🟢 {prix_o:.4f}")
            l3.write(f"{p_out_memo:.4f}" if p_out_memo > 0 else "---")
            l4.info("⏳ Attente ACHAT")
            l5.write(f"{(p_out_memo if p_out_memo > 0 else prix_o) * vol_o:.2f} USDC")
        else:
            l2.write(f"✅ {p_in_memo:.4f}" if p_in_memo > 0 else "✅ FAIT")
            l3.write(f"🔴 {prix_o:.4f}")
            l4.success("💰 Attente VENTE")
            l5.write(f"**{prix_o * vol_o:.2f} USDC**")
            
        if l6.button("❌", key=oid):
            k.query_private('CancelOrder', {'txid': oid})
            st.rerun()
        st.divider()
else:
    st.info("Aucun bot actif.")

# 6. RESET TOTAL
if st.sidebar.button("🗑️ TOUT ANNULER"):
    k.query_private('CancelAll')
    st.rerun()
