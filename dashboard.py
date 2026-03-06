# --- SECTION LISTE DES BOTS ACTIFS ---
st.write("---")
st.subheader("📋 État de ma Grille (Bots Lancés)")

try:
    # On récupère les ordres ouverts chez Kraken
    open_orders = k.query_private('OpenOrders')['result']['open']
    
    if open_orders:
        # On prépare les données pour le tableau
        data_bots = []
        for oid, details in open_orders.items():
            data_bots.append({
                "ID Bot": oid[:8], # On garde les 8 premiers caractères de l'ID
                "Action": details['descr']['type'].upper(),
                "Prix": f"{details['descr']['price']} USDC",
                "Volume": details['vol'],
                "Statut": details['status'].upper()
            })
        
        # On affiche le tableau Streamlit
        df = pd.DataFrame(data_bots)
        st.table(df) # Utilise st.table pour une liste fixe ou st.dataframe pour défiler
        
        st.write(f"✅ Total : **{len(open_orders)}** bots en attente sur le marché.")
    else:
        st.info("📭 Aucun bot actif. Ton solde est libre.")

except Exception as e:
    st.write("⏳ Chargement des ordres ou erreur de connexion...")
