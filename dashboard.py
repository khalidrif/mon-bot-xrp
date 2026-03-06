import streamlit as st
import krakenex

st.title("🎯 Bot XRP : Ordres Liés (Achat puis Vente)")

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 1. Infos Marché
res = k.query_public('Ticker', {'pair': 'XRPUSDC'})
prix_actuel = float(res['result']['XRPUSDC']['c'])
st.metric("Prix XRP actuel", f"{prix_actuel} USDC")

with st.form("bot_individuel"):
    st.write("### Configurer 1 Bot (Achat ➔ Vente automatique)")
    c1, c2, c3 = st.columns(3)
    p_achat = c1.number_input("Prix d'ACHAT souhaité", value=round(prix_actuel*0.99, 4), format="%.4f")
    p_vente = c2.number_input("Prix de VENTE (Profit)", value=round(prix_actuel*1.02, 4), format="%.4f")
    vol = c3.number_input("Quantité (XRP)", value=15.0)
    
    submit = st.form_submit_button("🚀 LANCER CE BOT")

if submit:
    try:
        # ON UTILISE 'close' : Cela crée un ordre de vente qui ne s'active 
        # QUE SI l'achat est rempli (Filled). C'est beaucoup plus propre !
        order_data = {
            'pair': 'XRPUSDC',
            'type': 'buy',
            'ordertype': 'limit',
            'price': str(p_achat),
            'volume': str(vol),
            'close[ordertype]': 'limit',
            'close[price]': str(p_vente),
            'close[pair]': 'XRPUSDC',
            'close[type]': 'sell'
        }
        
        res = k.query_private('AddOrder', order_data)
        
        if res.get('result'):
            st.success(f"✅ Bot programmé ! Achat à {p_achat}. La vente à {p_vente} s'activera toute seule après l'achat.")
            st.json(res['result']['txid'])
        else:
            st.error(f"Erreur Kraken : {res.get('error')}")
            
    except Exception as e:
        st.error(f"Erreur technique : {e}")

# Affichage des ordres
st.write("---")
st.write("### 📋 Mes ordres en attente")
try:
    open_orders = k.query_private('OpenOrders')['result']['open']
    if open_orders:
        st.write(open_orders)
    else:
        st.info("Aucun ordre en attente.")
except:
    st.write("Connexion en cours...")
