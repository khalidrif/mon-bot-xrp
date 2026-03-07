import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE PREMIUM AVEC COULEURS SPÉCIFIQUES
st.set_page_config(page_title="XRP Command Center", layout="centered")

st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); 
        color: #212529; 
    }
    
    /* Couleur du SOLDE DISPO (Bleu Électrique) */
    div[data-testid="stMetricValue"] { 
        font-weight: 800 !important;
        font-size: 2.2rem !important;
    }
    
    /* Ciblage spécifique pour les couleurs des métriques */
    [data-testid="stMetric"]:nth-of-type(1) div[data-testid="stMetricValue"] {
        color: #007AFF !important;
    }

    /* Couleur du PRIX XRP (Orange Marché) */
    [data-testid="stMetric"]:nth-of-type(2) div[data-testid="stMetricValue"] {
        color: #FF9500 !important;
    }

    .cumul-box { 
        background: linear-gradient(135deg, #28a745 0%, #218838 100%); 
        border-radius: 25px; padding: 25px; text-align: center; color: white; 
        margin-bottom: 25px; box-shadow: 0px 10px 20px rgba(40, 167, 69, 0.2);
    }

    div[data-testid="stMetric"] {
        background-color: white; padding: 15px; border-radius: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05); border: 1px solid #DEE2E6;
    }

    .stButton>button { 
        width: 100%; height: 65px; font-size: 22px !important; 
        border-radius: 20px !important; background-color: #F3BA2F !important;
        color: #000 !important; border: none !important; font-weight: bold;
    }
    input { height: 50px !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. MÉMOIRE DU PROFIT
if 'profit_total' not in st.session_state:
    st.session_state.profit_total = 0.0

# HEADER PROFIT CUMULÉ
st.markdown(f"""
    <div class="cumul-box">
        <p style="margin: 0; font-size: 0.9rem; font-weight: 500;">PROFIT TOTAL RÉALISÉ</p>
        <h1 style="margin: 0; font-size: 3.2rem; font-weight: 800;">+ {st.session_state.profit_total:.2f} $</h1>
    </div>
""", unsafe_allow_html=True)

try:
    # CONNEXION KRAKEN
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

    st.write("") 

    # 3. RÉGLAGES
    p_in = st.number_input("PRIX ACHAT", value=1.3600, format="%.4f")
    p_out = st.number_input("PRIX VENTE", value=1.3800, format="%.4f")
    vol = st.number_input("VOLUME XRP", value=21.0)

    # 4. ACTIONS
    if st.button("🚀 ACTIVER LE SNIPER"):
        params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
        kraken.create_limit_buy_order('XRP/USDC', vol, p_in, params)
        st.balloons()
        st.success("C'est parti !")

    if st.button("🚨 ANNULER TOUT / RESET"):
        st.session_state.profit_total = 0.0
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()

except Exception as e:
    st.error(f"Liaison : {e}")

time.sleep(30)
st.rerun()
