import streamlit as st
import krakenex
import numpy as np

st.title("🏗️ Constructeur de Grille Géante (100 Niveaux)")

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 1. Configuration de la zone de pêche
st.write("### ⚙️ Réglages de la Grille")
c1, c2, c3 = st.columns(3)
prix_max = c1.number_input("Prix du Haut (USDC)", value=1.50, format="%.4f")
prix_min = c2.number_input("Prix du Bas (USDC)", value=1.30, format="%.4f")
vol_lot = c3.number_input("XRP par niveau", value=11.0)

profit_pct = st.slider("Profit par palier (%)", 0.5, 5.0, 2.0) / 100

if st.button("🔥 DÉPLOYER LES 100 BOTS D'UN COUP"):
    # On calcule les 100 paliers de prix
    paliers = np.linspace(prix_min, prix_max, 100)
    
    barre_progression = st.progress(0)
    
    for i, p in enumerate(paliers):
        try:
            p_achat = round(p, 5)
            p_vente = round(p * (1 + profit_pct), 5)
            
            # On envoie l'ordre lié (Achat -> Vente)
            k.query_private('AddOrder', {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit',
                'price': str(p_achat), 'volume': str(vol_lot),
                'close[ordertype]': 'limit', 'close[price]': str(p_vente),
                'close[type]': 'sell'
            })
        except Exception:
            pass # On ignore si un palier échoue (solde etc.)
            
        barre_progression.progress((i + 1) / 100)
    
    st.success(f"🎯 Grille de 100 niveaux déployée entre {prix_min} et {prix_max} !")

# 2. Liste compacte des ordres
st.write("---")
if st.checkbox("👁️ Afficher mes 100+ ordres actifs"):
    try:
        res = k.query_private('OpenOrders')['result']['open']
        st.write(f"Tu as actuellement **{len(res)}** ordres ouverts.")
        st.json(res)
    except:
        st.write("Chargement...")
