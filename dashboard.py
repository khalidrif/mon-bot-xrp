import streamlit as st
import krakenex
import pandas as pd

st.set_page_config(page_title="Kraken Snowball", layout="wide")
st.title("❄️ XRP Snowball : Traqueur de Gains")

# 1. Mémoire des gains (Initialisation)
if 'profit_total' not in st.session_state:
    st.session_state.profit_total = 0.0

# 2. Connexion
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 3. Récupérer Prix et Ordres
try:
    res_ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    # Correction extraction du prix (premier élément de la liste 'c')
    prix_actuel = float(res_ticker['result']['XRPUSDC']['c'][0])
    
    res_open = k.query_private('OpenOrders')['result']['open']
    prix_deja_poses = [float(det['descr']['price']) for det in res_open.values()]
    
    # --- AFFICHAGE DES SCORES ---
    c1, c2 = st.columns(2)
    c1.metric("Prix XRP actuel", f"{prix_actuel} USDC")
    c2.metric("💰 PROFIT CUMULÉ (Session)", f"+{st.session_state.profit_total:.4f} USDC", delta="Boule de neige ❄️")

except Exception as e:
    st.error(f"Erreur technique : {e}")
    prix_actuel = 1.40
    res_open = {}

# 4. Formulaire Boule de Neige
with st.form("bot_snowball"):
    st.write("### ➕ Lancer un Bot (Réinvestissement)")
    col1, col2, col3 = st.columns(3)
    p_achat = col1.number_input("Prix Achat", value=round(prix_actuel*0.99, 4), format="%.4f")
    p_vente = col2.number_input("Prix Vente", value=round(prix_actuel*1.02, 4), format="%.4f")
    # On suggère un volume qui utilise le profit précédent !
    vol_suggere = 11.0 + (st.session_state.profit_total / prix_actuel)
    vol = col3.number_input("Volume (XRP)", value=round(vol_suggere, 1))
    
    # Calcul profit estimé
    frais = (p_achat * vol * 0.0026) + (p_vente * vol * 0.0026)
    gain_net = ((p_vente - p_achat) * vol) - frais
    st.info(f"📈 Ce bot va générer **+{gain_net:.4f} USDC** de profit net.")
    
    submit = st.form_submit_button("🚀 LANCER ET AJOUTER À LA BOULE")

if submit:
    if any(abs(p - p_achat) < 0.0001 for p in prix_deja_poses):
        st.warning(f"⚠️ Prix déjà utilisé !")
    else:
        try:
            # Ordre lié Achat -> Vente
            order_data = {
                'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(vol),
                'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'
            }
            k.query_private('AddOrder', order_data)
            
            # On simule l'ajout au profit futur (pour voir la boule grossir)
            st.session_state.profit_total += gain_net
            st.success(f"✅ Bot programmé ! Profit total visé : {st.session_state.profit_total:.4f}")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur Kraken : {e}")

# 5. Liste des ordres
st.write("---")
if res_open:
    st.write(f"### 📋 Bots en cours ({len(res_open)})")
    data = [{"ID": k[:6], "Type": v['descr']['type'].upper(), "Prix": v['descr']['price'], "Vol": v['vol']} for k, v in res_open.items()]
    st.table(pd.DataFrame(data))
else:
    st.info("Aucun bot actif.")

if st.button("🗑️ TOUT ANNULER"):
    k.query_private('CancelAll')
    st.session_state.profit_total = 0.0 # On remet à zéro
    st.rerun()
