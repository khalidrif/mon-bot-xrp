import streamlit as st
import krakenex
import time

# 1. STYLE JAUNE & NOIR (Style Bitget/Binance)
st.set_page_config(page_title="XRP Gold Snowball", layout="centered")
st.markdown("""
    <style>
    /* Fond noir profond */
    .stApp { background-color: #000000; color: #F3BA2F; }
    
    /* Metrics en Jaune Gold */
    div[data-testid="stMetric"] { 
        background-color: #121212; 
        border: 1px solid #F3BA2F; 
        padding: 15px; 
        border-radius: 10px; 
    }
    [data-testid="stMetricValue"] { color: #F3BA2F !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; }

    /* Inputs et Boutons */
    label[data-testid="stWidgetLabel"] { color: #F3BA2F !important; font-weight: bold; }
    .stButton>button { 
        background-color: #F3BA2F !important; 
        color: black !important; 
        border: none !important;
        font-weight: bold !important;
    }
    .stButton>button:hover { background-color: #FFD700 !important; }
    
    /* Input background */
    input { background-color: #121212 !important; color: white !important; border: 1px solid #F3BA2F !important; }
    </style>
    """, unsafe_allow_html=True)

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# 2. DONNÉES EN HAUT
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})['result']['XRPUSDC']
    prix_actuel = float(ticker['c'][0])
    bal = k.query_private('Balance')['result']
    usdc = float(bal.get('USDC', 0))
    
    st.markdown("<h1 style='text-align: center; color: #F3BA2F;'>🟡 XRP GOLD BOT</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("PRIX XRP", f"{prix_actuel:.4f} $")
    c2.metric("SOLDE DISPONIBLE", f"{usdc:.2f} USDC")
except:
    st.error("Connexion Kraken en cours...")

st.markdown("<hr style='border: 0.5px solid #F3BA2F;'>", unsafe_allow_html=True)

# 3. RÉGLAGES
p_in = st.number_input("PRIX ACHAT (Bas)", value=1.3600, format="%.4f")
p_out = st.number_input("PRIX VENTE (Haut)", value=1.4000, format="%.4f")

if 'run' not in st.session_state: st.session_state.run = False

col_run, col_stop = st.columns(2)
if col_run.button("▶️ DÉMARRER LE BOT", use_container_width=True):
    st.session_state.run = True

if col_stop.button("⏹️ ARRÊTER & ANNULER", use_container_width=True):
    st.session_state.run = False
    k.query_private('CancelAll')
    st.rerun()

# 4. MOTEUR SNOWBALL
status = st.empty()
if st.session_state.run:
    try:
        ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})
        if not ordres:
            # Calcul du volume avec tes USDC
            vol = (usdc * 0.98) / p_in
            if vol >= 10:
                params = {
                    'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(round(vol, 1)),
                    'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'
                }
                k.query_private('AddOrder', params)
                status.success(f"✅ Nouveau cycle : {vol:.1f} XRP envoyés")
            else:
                status.error("Solde trop faible (< 10 XRP)")
        else:
            for oid, det in ordres.items():
                status.warning(f"🟡 EN MISSION : {det['descr']['order']}")
    except Exception as e:
        status.error(f"API Error: {e}")

    time.sleep(15)
    st.rerun()
