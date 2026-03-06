import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration
st.set_page_config(page_title="XRP Line Tracker", layout="wide")
st.title("🛡️ Console de Trading XRP (Vue par Lignes)")

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
with st.expander("➕ LANCER UN NOUVEAU BOT", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    p_in = c1.number_input("ACHAT (Bas)", value=1.0400, format="%.4f")
    p_out = c2.number_input("VENTE (Haut)", value=1.5000, format="%.4f")
    vol = c3.number_input("Quantité XRP", value=12.0)
    
    if c4.button("🚀 ACTIVER", use_container_width=True):
        id_tentative = f"{p_in}-{p_out}-{vol}"
        if st.session_state.dernier_ordre == id_tentative:
            st.warning("⚠️ Déjà envoyé !")
        else:
            try:
                memo = int(p_in * 10000) # Mémoire du prix d'entrée
                k.query_private('AddOrder', {
                    'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(vol),
                    'userref': str(memo),
                    'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
                })
                st.session_state.dernier_ordre = id_tentative
                st.rerun()
            except: st.error("Erreur Kraken")

st.write("---")

# 5. AFFICHAGE PAR LIGNES (Une ligne par Bot)
st.subheader(f"🤖 Mes Bots Actifs ({len(ordres_ouverts)})")

if ordres_ouverts:
    # En-tête des colonnes
    h1, h2, h3, h4, h5 = st.columns([1, 2, 2, 2, 1])
    h1.write("**Bot**")
    h2.write("**Prix ENTRÉE**")
    h3.write("**Prix SORTIE**")
    h4.write("**ÉTAT**")
    h5.write("**ACTION**")

    for i, (oid, det) in enumerate(ordres_ouverts.items(), start=1):
        type_o = det['descr']['type'].upper()
        prix_o = float(det['descr']['price'])
        
        # Récupération du prix d'entrée mémorisé
        try:
            p_in_memo = int(det.get('userref', 0)) / 10000
        except: p_in_memo = 0.0

        # Organisation d'une ligne
        l1, l2, l3, l4, l5 = st.columns([1, 2, 2, 2, 1])
        
        l1.write(f"#{i}")
        
        # Colonne ENTRÉE
        if type_o == "BUY":
            l2.write(f"⏳ {prix_o:.4f}")
            l3.write("---")
            l4.info("📦 Attente Achat")
        else:
            l2.write(f"✅ {p_in_memo:.4f}" if p_in_memo > 0 else "✅ FAIT")
            l3.write(f"🎯 {prix_o:.4f}")
            l4.success("💰 Attente Vente")
            
        # Bouton STOP
        if l5.button("❌", key=oid):
            k.query_private('CancelOrder', {'txid': oid})
            st.rerun()
        st.write("---") # Séparateur entre les bots
else:
    st.info("Aucun bot actif.")

# 6. RESET TOTAL
if st.sidebar.button("🗑️ TOUT ANNULER"):
    k.query_private('CancelAll')
    st.rerun()
