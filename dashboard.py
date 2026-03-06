import streamlit as st
import krakenex
import time

# 1. STYLE NOIR & CYAN
st.set_page_config(page_title="XRP Snowball", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    div[data-testid="stMetric"] { background-color: #161B22; border: 1px solid #30363D; padding: 15px; border-radius: 10px; }
    label[data-testid="stWidgetLabel"] { color: #58A6FF !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 2. DONNÉES EN HAUT
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})['result']['XRPUSDC']
    prix_actuel = float(ticker['c'][0])
    bal = k.query_private('Balance')['result']
    usdc = float(bal.get('USDC', 0))
    
    st.title("❄️ XRP SNOWBALL")
    c1, c2 = st.columns(2)
    c1.metric("PRIX XRP", f"{prix_actuel:.4f} $")
    c2.metric("TON SOLDE", f"{usdc:.2f} USDC")
except:
    st.error("Connexion Kraken...")

st.divider()

# 3. RÉGLAGES & BOUTONS
p_in = st.number_input("ACHAT (Prix Bas)", value=1.3600, format="%.4f")
p_out = st.number_input("VENTE (Prix Haut)", value=1.4000, format="%.4f")

if 'run' not in st.session_state: st.session_state.run = False

col_run, col_stop = st.columns(2)
if col_run.button("▶️ LANCER", use_container_width=True, type="primary"):
    st.session_state.run = True
if col_stop.button("⏹️ STOP", use_container_width=True):
    st.session_state.run = False
    k.query_private('CancelAll')
    st.rerun()

# 4. MOTEUR SIMPLE
status = st.empty()
if st.session_state.run:
    try:
        ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})
        if not ordres:
            # Calcule le volume avec tes 29$ (ou ton nouveau solde)
            vol = (usdc * 0.98) / p_in
            if vol >= 10:
                params = {
                    'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(round(vol, 1)),
                    'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
                }
                k.query_private('AddOrder', params)
                status.success(f"✅ Nouveau cycle : {vol:.1f} XRP envoyés")
            else:
                status.error("Solde insuffisant (min 10 XRP)")
        else:
            for oid, det in ordres.items():
                status.info(f"⏳ MISSION : {det['descr']['order']}")
    except Exception as e:
        status.error(f"API : {e}")

    time.sleep(15)
    st.rerun()
