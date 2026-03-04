# --- 1. STYLE "TERMINAL STATIQUE" (BLOQUE LA VAGUE) ---
st.set_page_config(page_title="XRP Bloomberg Fixed", layout="wide")
st.markdown("""
    <style>
    /* Empêche le défilement et stabilise la page */
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden;
        background-color: #000000;
    }
    .main { background-color: #000000; color: #FFFFFF; font-family: 'Courier New', monospace; }
    
    /* Fixe les cartes de prix en haut */
    [data-testid="stMetric"] { 
        background-color: #FFFF00 !important; 
        border-radius: 5px; 
        padding: 10px; 
        border: 1px solid #333;
        transition: none !important; /* Supprime l'animation de mise à jour */
    }
    [data-testid="stMetricValue"] { color: #000000 !important; font-size: 24px !important; font-weight: 900 !important; }
    
    /* Lignes des bots ultra-stables */
    .bot-line { 
        border-bottom: 1px solid #222222; 
        padding: 8px 0px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        font-size: 13px;
        min-height: 40px; /* Force une hauteur constante */
    }
    .flash-box { background-color: #FFFF00; color: #000000; padding: 2px 6px; border-radius: 2px; font-weight: 900; }
    
    /* Supprime l'icône de chargement en haut à droite */
    [data-testid="stStatusWidget"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
