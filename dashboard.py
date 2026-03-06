import streamlit as st
import krakenex
import pandas as pd

# 1. Connexion et Configuration
st.set_page_config(page_title="Kraken Grid Tracker", layout="wide")
st.title("❄️ XRP Snowball : État de la Grille")

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 2. Récupération des données
try:
    # Prix actuel
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    
    # Ordres Ouverts
    res_open = k.query_private('OpenOrders')['result']['open']
    
    # Affichage des indicateurs
    c1, c2 = st.columns(2)
    c1.metric("Prix XRP actuel", f"{prix_actuel} USDC")
    c2.metric("Bots Actifs", len(res_open))

    # 3. TRANSFORMATION EN TABLEAU CLAIR
    if res_open:
        st.write("### 📋 Liste de mes Bots (Achats & Ventes)")
        
        # On prépare les colonnes proprement
        liste_bots = []
        for oid, details in res_open.items():
            type_ordre = details['descr']['type'].upper()
            prix_ordre = float(details['descr']['price'])
            volume = float(details['vol'])
            
            # Calcul du profit visé pour cet ordre spécifique
            profit_vise = "---"
            if type_ordre == "SELL":
                # Si c'est une vente, on affiche le gain net quand elle touchera
                profit_vise = f"+{(prix_ordre * volume * 0.98) - (prix_actuel * volume):.2f} USDC"

            liste_bots.append({
                "ID Bot": oid[:6],
                "Action": "📥 ACHAT" if type_ordre == "BUY" else "💰 VENTE (Profit)",
                "Prix Cible": f"{prix_ordre:.4f} USDC",
                "Quantité": f"{volume} XRP",
                "Profit Estimé": profit_vise
            })

        df = pd.DataFrame(liste_bots)
        
        # Affichage avec couleurs et défilement
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("Aucun bot ne tourne actuellement. Ton filet de pêche est vide.")

except Exception as e:
    st.error(f"Erreur d'affichage : {e}")

# 4. Bouton de nettoyage
if st.button("🗑️ TOUT ANNULER"):
    k.query_private('CancelAll')
    st.rerun()
