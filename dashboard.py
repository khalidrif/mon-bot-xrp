import streamlit as st
import krakenex
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="Kraken Snowball Bot", layout="wide")
st.title("❄️ XRP Snowball : Console de Trading")

# Initialisation de la mémoire du profit (Session)
if 'profit_cumule' not in st.session_state:
    st.session_state.profit_cumule = 0.0

# 2. Connexion à Kraken
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Récupération des données en temps réel
try:
    # Prix actuel (Extraction propre de la liste)
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    
    # Ordres Ouverts
    res_open = k.query_private('OpenOrders')['result']['open']
    prix_deja_poses = [float(det['descr']['price']) for det in res_open.values()]
    
    # Affichage des compteurs en haut
    c1, c2, c3 = st.columns(3)
    c1.metric("🚀 Prix XRP actuel", f"{prix_actuel:.4f} USDC")
    c2.metric("💰 Profit Cumulé (Session)", f"+{st.session_state.profit_cumule:.4f} USDC", delta="Boule de neige ❄️")
    c3.metric("🤖 Bots Actifs", len(res_open))

except Exception as e:
    st.error(f"⚠️ Erreur de connexion : {e}")
    prix_actuel = 1.40
    res_open = {}
    prix_deja_poses = []

# 4. Formulaire de lancement "Boule de Neige"
st.write("---")
with st.form("form_bot"):
    st.subheader("➕ Lancer un nouveau Bot Individuel")
    col1, col2, col3 = st.columns(3)
    
    p_achat = col1.number_input("Prix d'ACHAT (USDC)", value=round(prix_actuel*0.99, 4), format="%.4f")
    p_vente = col2.number_input("Prix de VENTE (USDC)", value=round(prix_actuel*1.02, 4), format="%.4f")
    
    # Suggestion de volume (Boule de neige : utilise le profit pour augmenter la taille)
    vol_base = 12.0 
    vol = col3.number_input("Volume (XRP)", value=vol_base, step=1.0)
    
    # Calcul du GAIN NET (Prix Vente - Prix Achat * Vol) - Frais estimés (0.26% x 2)
    frais_estimes = (p_achat * vol * 0.0026) + (p_vente * vol * 0.0026)
    gain_net = ((p_vente - p_achat) * vol) - frais_estimes
    
    st.info(f"📈 Prévision : Ce bot générera **+{gain_net:.4f} USDC** de profit net.")
    
    submit = st.form_submit_button("🚀 ACTIVER LE BOT")

# Logique d'activation
if submit:
    # Sécurité anti-double
    if any(abs(p - p_achat) < 0.0001 for p in prix_deja_poses):
        st.warning(f"⚠️ Action bloquée : Un bot existe déjà à {p_achat} USDC.")
    else:
        try:
            # Ordre lié (If Done) : Achat -> Vente automatique
            order_data = {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
                'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
            }
            k.query_private('AddOrder', order_data)
            
            # Mise à jour de la boule de neige (cumul théorique)
            st.session_state.profit_cumule += gain_net
            st.success(f"✅ Bot programmé ! Profit total visé : {st.session_state.profit_cumule:.4f}")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur Kraken : {e}")

# 5. Tableau de bord des Bots lancés
st.write("---")
st.subheader("📦 Ma Grille de Trading")

if res_open:
    liste_affichage = []
    for oid, det in res_open.items():
        type_o = det['descr']['type'].upper()
        p_o = float(det['descr']['price'])
        v_o = float(det['vol'])
        
        # Calcul du gain spécifique à cette ligne
        gain_ligne = "En attente d'achat..."
        if type_o == "SELL":
            gain_ligne = f"+{gain_net:.2f} USDC"

        liste_affichage.append({
            "ID": oid[:6],
            "Action": "📥 ACHAT" if type_o == "BUY" else "💰 VENTE (Profit)",
            "Prix Cible": f"{p_o:.4f} USDC",
            "Quantité": f"{v_o} XRP",
            "Profit Net": gain_ligne
        })
    
    df = pd.DataFrame(liste_affichage)
    st.dataframe(df, use_container_width=True, height=400)
else:
    st.info("Aucun bot actif pour le moment.")

# 6. Bouton de nettoyage global
if st.sidebar.button("🗑️ TOUT ANNULER (RESET)"):
    k.query_private('CancelAll')
    st.session_state.profit_cumule = 0.0
    st.rerun()
