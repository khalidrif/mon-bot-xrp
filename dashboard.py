import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration
st.set_page_config(page_title="XRP Fourchette Bot", layout="wide")
st.title("❄️ XRP Snowball : Gestion par Fourchettes")

# Initialisation du profit session
if 'profit_session' not in st.session_state:
    st.session_state.profit_session = 0.0

# 2. Connexion Kraken
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Données Marché
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    # Correction de l'extraction du prix
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    res_open = k.query_private('OpenOrders')['result']['open']
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    c2.metric("💰 Profit Cumulé", f"+{st.session_state.profit_session:.2f} USDC")
    c3.metric("🤖 Bots en cours", len(res_open))
except:
    st.error("Connexion Kraken impossible.")
    prix_actuel = 1.40
    res_open = {}

# 4. FORMULAIRE : CONFIGURATION DE LA FOURCHETTE
st.write("---")
with st.form("form_bot"):
    st.subheader("➕ Définir une Fourchette de Trading (Bot Individuel)")
    col1, col2, col3 = st.columns(3)
    
    # Case Prix d'Achat et Vente
    p_achat = col1.number_input("ACHAT (Bas de fourchette)", value=1.0400, format="%.4f")
    p_vente = col2.number_input("VENTE (Haut de fourchette)", value=1.5000, format="%.4f")
    vol = col3.number_input("Quantité (XRP)", value=12.0)
    
    # Calcul des gains pour affichage
    frais = (p_achat * vol * 0.0026) + (p_vente * vol * 0.0026)
    profit_net = ((p_vente - p_achat) * vol) - frais
    montant_total_recupere = (p_vente * vol) - (p_vente * vol * 0.0026)
    
    st.info(f"📊 **Analyse :** Fourchette {p_achat} - {p_vente} | **Profit Net :** +{profit_net:.2f} USDC | **Montant récupéré final :** {montant_total_recupere:.2f} USDC")
    
    submit = st.form_submit_button("🚀 LANCER CE BOT")

if submit:
    try:
        # Ordre lié : Achat -> Vente automatique
        order_data = {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
            'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
        }
        k.query_private('AddOrder', order_data)
        st.session_state.profit_session += profit_net
        st.success(f"✅ Bot programmé sur la fourchette {p_achat} - {p_vente}")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur Kraken : {e}")

# 5. TABLEAU DE BORD COLORÉ
st.write("---")
st.subheader("📋 Liste des Bots et Fourchettes actives")

if res_open:
    data_display = []
    for oid, det in res_open.items():
        type_actuel = det['descr']['type'].upper()
        prix_cible = float(det['descr']['price'])
        quantite = float(det['vol'])
        
        # On affiche l'état et la valeur attendue
        etat = "🟢 ATTENTE ACHAT" if type_actuel == "BUY" else "🔴 ATTENTE VENTE"
        
        # On calcule le montant + profit (Valeur finale du bot)
        # Si c'est un achat, on se base sur le prix de vente futur estimé (p_vente du formulaire)
        # Pour faire simple, on affiche la valeur à l'exécution de l'ordre actuel
        valeur_etape = prix_cible * quantite

        data_display.append({
            "Bot ID": oid[:6],
            "État": etat,
            "Fourchette / Prix": f"{prix_cible:.4f} USDC",
            "Volume": f"{quantite} XRP",
            "Montant + Profit": f"{valeur_etape:.2f} USDC",
            "_style": type_actuel
        })
    
    df = pd.DataFrame(data_display)

    # Application du style Vert (Achat) / Rouge (Vente)
    def style_rows(row):
        if row['_style'] == 'BUY':
            return ['background-color: rgba(46, 204, 113, 0.2)'] * len(row)
        else:
            return ['background-color: rgba(231, 76, 60, 0.2)'] * len(row)

    st.dataframe(
        df.style.apply(style_rows, axis=1),
        use_container_width=True,
        column_order=("Bot ID", "État", "Fourchette / Prix", "Volume", "Montant + Profit")
    )
else:
    st.info("Aucun bot actif. Configurez une fourchette ci-dessus.")

# 6. RESET TOTAL (En dehors du tableau)
st.write("---")
if st.button("🗑️ RESET TOTAL (Annuler tous les ordres)", use_container_width=True):
    k.query_private('CancelAll')
    st.session_state.profit_session = 0.0
    st.rerun()
