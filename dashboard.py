import streamlit as st
import krakenex
import time

# 1. STYLE BLANC & GRIS CLAIR
st.set_page_config(page_title="XRP White Snowball", layout="centered")
st.markdown("""
    <style>
    /* Fond blanc et texte noir */
    .stApp { background-color: #FFFFFF; color: #1E1E1E; }
    
    /* Metrics avec bordure grise discrète */
    div[data-testid="stMetric"] { 
        background-color: #F8F9FA; 
        border: 1px solid #E0E0E0; 
        padding: 15px; 
        border-radius: 12px; 
    }
    [data-testid="stMetricValue"] { color: #007BFF !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #6C757D !important; }

    /* Inputs et Boutons */
    label[data-testid="stWidgetLabel"] { color: #1E1E1E !important; font-weight: bold; }
    .stButton>button { 
        background-color: #007BFF !important; 
        color: white !important; 
        border-radius: 8px !important;
        font-weight: bold !important;
        border: none !important;
    }
    .stButton>button:hover { background-color: #0056B3 !important; }
    
    /* Barre de statut */
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 2. DONNÉES EN HAUT
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})['result']['XRPUSDC']
    prix_actuel = float(ticker['c'])
    bal = k.query_private('Balance')['result']
    usdc = float(bal.get('USDC', 0))
    
    st.markdown("<h1 style='text-align: center; color: #1E1E1E;'>📊 XRP WHITE BOT</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("PRIX XRP", f"{prix_actuel:.4f} $")
    c2.metric("MON SOLDE", f"{usdc:.2f} USDC")
except:
    st.info("Connexion Kraken...")

st.markdown("<hr style='border: 0.5px solid #E0E0E0;'>", unsafe_allow_html=True)

# 3. RÉGLAGES
p_in = st.number_input("ACHAT (Prix Bas)", value=1.3600, format="%.4f")
p_out = st.number_input("VENTE (Prix Haut)", value=1.4000, format="%.4f")

if 'run' not in st.session_state: st.session_state.run = False

col_run, col_stop = st.columns(2)
if col_run.button("▶️ DÉMARRER LE CYCLE", use_container_width=True):
    st.session_state.run = True

if col_stop.button("⏹️ ARRÊTER TOUT", use_container_width=True):
    st.session_state.run = False
    k.query_private('CancelAll')
    st.rerun()

# 4. MOTEUR
status = st.empty()
if st.session_state.run:
    try:
        ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})
        if not ordres:
            # Calcul du volume avec tes 29$ + profits
            vol = (usdc * 0.98) / p_in
            if vol >= 10:
                params = {
                    'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(round(vol, 1)),
                    'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
                }
                k.query_private('AddOrder', params)
                status.success(f"✅ Nouveau cycle : {vol:.1f} XRP envoyés")
            else:
                status.error("Solde trop faible pour racheter.")
        else:
            for oid, det in ordres.items():
                status.info(f"⏳ EN MISSION : {det['descr']['order']}")
    except Exception as e:
        status.error(f"API Error: {e}")

    time.sleep(15)
    st.rerun()
