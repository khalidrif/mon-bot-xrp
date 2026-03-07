import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM (Fond Soft Grey / Blanc)
st.set_page_config(page_title="XRP Command Center", layout="centered")

st.markdown("""
    <style>
    /* Fond principal dégradé léger pour ne pas fatiguer les yeux */
    .stApp { 
        background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); 
        color: #212529; 
    }
    
    /* Boîte de Profit Cumulé (Style iOS Notification) */
    .cumul-box { 
        background: linear-gradient(135deg, #28a745 0%, #218838 100%); 
        border-radius: 25px; 
        padding: 25px; 
        text-align: center; 
        color: white; 
        margin-bottom: 25px;
        box-shadow: 0px 10px 20px rgba(40, 167, 69, 0.2);
    }

    /* Cartes de métriques blanches et bombées */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        border: 1px solid #DEE2E6;
    }

    /* Boutons tactiles larges */
    .stButton>button { 
        width: 100%; 
        height: 65px; 
        font-size: 22px !important; 
        border-radius: 20px !important; 
        background-color: #F3BA2F !important; /* Jaune Binance */
        color: #000 !important; 
        border: none !important; 
        font-weight: bold;
        box-shadow: 0px 5px 15px rgba(243, 186, 47, 0.3);
    }

    /* Inputs plus larges pour les doigts */
    input { 
        height: 55px !important; 
        border-radius: 12px !important; 
        font-size: 18px !important;
        border: 1px solid #CED4DA !important;
    }

    h1, h2, h3 { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica; }
    </style>
    """, unsafe_allow_html=True)

# 2. MÉMOIRE DU PROFIT
if 'profit_total' not in st.session_state:
    st.session_state.profit_total = 0.0

# HEADER
st.markdown(f"""
    <div class="cumul-box">
        <p style="margin: 0; font-size: 0.9rem; font-weight: 500;">PROFIT TOTAL RÉALISÉ</p>
        <h1 style="margin: 0; font-size: 3.2rem; font-weight: 800;">+ {st.session_state.profit_total:.2f} $</h1>
    </div>
""", unsafe_allow_html=True)

try:
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })

    # Données Live
    balance = kraken.fetch_balance()
    usdc_reel = balance['total'].get('USDC', 0.0)
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last'])

    col1, col2 = st.columns(2)
    col1.metric("DISPO USDC", f"{usdc_reel:.2f} $")
    col2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.write("") # Espacement

    # 3. RÉGLAGES (1.36 / 1.38)
    with st.container():
        st.markdown("<p style='font-weight: bold; margin-bottom: -10px;'>PARAMÈTRES DU CYCLE</p>", unsafe_allow_html=True)
        p_in = st.number_input("PRIX ACHAT", value=1.3600, format="%.4f")
        p_out = st.number_input("PRIX VENTE", value=1.3800, format="%.4f")
        vol = st.number_input("VOLUME XRP", value=21.0)

    # Calcul Profit
    frais = ((vol * p_in) + (vol * p_out)) * 0.0026
    gain_net = (vol * (p_out - p_in)) - frais
    
    st.info(f"💰 Gain net attendu : **{gain_net:.2f} $**")

    # 4. ACTIONS
    if st.button("🚀 ACTIVER LE SNIPER"):
        params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
        kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
        st.session_state.profit_total += gain_net
        st.balloons()
        st.success("C'est parti ! Profit ajouté au compteur.")

    if st.button("🚨 ANNULER TOUT / RESET"):
        st.session_state.profit_total = 0.0
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Liaison : {e}")

time.sleep(30)
st.rerun()
