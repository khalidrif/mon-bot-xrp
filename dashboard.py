import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE (Jaune & Noir, Gros Boutons)
st.set_page_config(page_title="XRP Pocket Command", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #F3BA2F; }
    [data-testid="stMetricValue"] { color: #F3BA2F !important; font-size: 1.8rem !important; }
    .stButton>button { 
        width: 100%; height: 60px; font-size: 20px !important; 
        border-radius: 15px !important; background-color: #F3BA2F !important;
        color: black !important; border: none !important; font-weight: bold;
    }
    input { background-color: #121212 !important; color: white !important; border: 1px solid #F3BA2F !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🟡 XRP COMMAND : 29$")

# 2. CONNEXION SÉCURISÉE CCXT
try:
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })

    # Récupération du solde et du prix (Anti-division par zéro)
    balance = kraken.fetch_balance()
    usdc_reel = balance['total'].get('USDC', 0.0)
    
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = float(ticker['last']) if ticker['last'] else 1.3500
    
    col1, col2 = st.columns(2)
    col1.metric("DISPO", f"{usdc_reel:.2f} $")
    col2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. CONFIGURATION (Réglé sur 1 bot par défaut pour tes 29$)
    n_grids = st.number_input("NOMBRE DE BOTS (Paliers)", value=1, min_value=1, max_value=50)
    p_min = st.number_input("PRIX ACHAT", value=1.3500, format="%.4f")
    p_out = st.number_input("PRIX VENTE", value=1.4000, format="%.4f")

    # --- CALCUL VOLUME ANTI-CRASH ---
    # On s'assure que prix_actuel et n_grids ne sont jamais à zéro
    if prix_actuel > 0 and n_grids > 0:
        vol_calcule = (usdc_reel * 0.98 / n_grids) / prix_actuel
    else:
        vol_calcule = 10.5 # Minimum de sécurité Kraken

    # On affiche le volume final (on force à 10.5 minimum pour éviter l'erreur Kraken)
    vol_final = st.number_input("VOLUME XRP PAR BOT", value=max(float(round(vol_calcule, 1)), 10.5))

    # 4. LE BOUTON DE LANCEMENT
    if st.button("🚀 DÉPLOYER LA MISSION"):
        # On vérifie si on a assez d'USDC
        if usdc_reel < (vol_final * p_min):
            st.error(f"Solde insuffisant ! Il te faut env. {(vol_final * p_min):.2f}$")
        else:
            try:
                # Envoi de l'ordre d'achat avec VENTE automatique (Take Profit)
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol_final, p_min, params)
                st.balloons()
                st.success(f"✅ BOT Lancé : Achat à {p_min}$ / Vente à {p_out}$")
            except Exception as e:
                st.error(f"Erreur Kraken : {e}")

    # 5. BOUTON PANIQUE
    st.write("")
    if st.button("🚨 ANNULER TOUT / RESET"):
        kraken.cancel_all_orders('XRP/USDC')
        st.warning("Ordres annulés. Solde libéré.")
        st.rerun()

except Exception as e:
    st.error(f"❌ Connexion impossible : {e}")

# Refresh toutes les 30 sec
time.sleep(30)
st.rerun()
