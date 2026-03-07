import streamlit as st
import ccxt
import time

# 1. STYLE IPHONE/PC (Jaune & Noir)
st.set_page_config(page_title="XRP 50-GRID COMMAND", layout="wide")
st.markdown("<style>.stApp { background-color: #000; color: #F3BA2F; }</style>", unsafe_allow_html=True)

st.title("⚡ XRP MEGA-GRID : 50 BOTS")

try:
    # 2. CONNEXION SÉCURISÉE
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })

    # Récupération du solde
    balance = kraken.fetch_balance()
    usdc_reel = balance['total'].get('USDC', 0.0)
    
    c1, c2 = st.columns(2)
    c1.metric("SOLDE DISPO", f"{usdc_reel:.2f} USDC")

    # Prix Live
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = ticker['last']
    c2.metric("PRIX XRP", f"{prix_actuel:.4f} $")

    st.divider()

    # 3. CONFIGURATION UNIQUE
    col_a, col_b, col_c = st.columns(3)
    p_min = col_a.number_input("PRIX BAS", value=1.3000, format="%.4f")
    p_max = col_b.number_input("PRIX HAUT", value=1.4500, format="%.4f")
    n_grids = col_c.number_input("NBRE BOTS", value=50)

    # Volume par bot (3000$ / 50 = ~60$ soit env 44 XRP)
    vol_per_bot = (usdc_reel * 0.98 / n_grids) / prix_actuel if usdc_reel > 10 else 44.0

    # 4. LE GROS BOUTON
    if st.button("🚀 DÉPLOYER LA GRILLE (3000$)", type="primary", use_container_width=True):
        step = (p_max - p_min) / (n_grids - 1)
        barre = st.progress(0)
        
        for i in range(int(n_grids)):
            target_price = round(p_min + (i * step), 4)
            try:
                if target_price < prix_actuel:
                    kraken.create_limit_buy_order('XRP/USDC', vol_per_bot, target_price)
                else:
                    kraken.create_limit_sell_order('XRP/USDC', vol_per_bot, target_price)
                
                time.sleep(0.5) # Anti-ban API
                barre.progress((i + 1) / n_grids)
            except Exception as e:
                st.error(f"Erreur palier {target_price}: {e}")
        
        st.balloons()
        st.success(f"✅ Armée de {n_grids} bots déployée !")

    st.divider()
    
    # 5. BOUTON PANIQUE
    if st.button("🚨 ANNULER TOUT ET STOP", use_container_width=True):
        kraken.cancel_all_orders('XRP/USDC')
        st.warning("Tous les ordres ont été supprimés.")
        st.rerun()

except Exception as e:
    st.error(f"❌ Connexion impossible : {e}")

# Auto-refresh toutes les 30 secondes
time.sleep(30)
st.rerun()
