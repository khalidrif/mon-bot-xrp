st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%); 
        color: #212529; 
    }
    
    /* Couleur du SOLDE DISPO (Bleu Pro) */
    [data-testid="stMetricLabel"]:nth-of-type(1) { color: #000000 !important; }
    div[data-testid="stMetricValue"]:nth-of-type(1) { 
        color: #007AFF !important; 
        font-weight: 800 !important;
        font-size: 2.2rem !important;
    }

    /* Couleur du PRIX XRP (Orange Marché) */
    [data-testid="stMetricLabel"]:nth-of-type(2) { color: #000000 !important; }
    div[data-testid="stMetricValue"]:nth-of-type(2) { 
        color: #FF9500 !important; 
        font-weight: 800 !important;
        font-size: 2.2rem !important;
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
    </style>
    """, unsafe_allow_html=True)
