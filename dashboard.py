import streamlit as st
import ccxt
import time

# 1. STYLE JAUNE & NOIR (Look Pro iPhone/PC)
st.set_page_config(page_title="XRP 50-GRID COMMAND", layout="wide")
st.markdown("<style>.stApp { background-color: #000; color: #F3BA2F; }</style>", unsafe_allow_html=True)

st.title("⚡ XRP MEGA-GRID : 50 BOTS")

# 2. CONNEXION SÉCURISÉE (CCXT)
try:
    # --- VÉRIFIE BIEN CES NOMS DANS TES SECRETS STREAMLIT ---
    kraken = ccxt.kraken({
        'apiKey': st.secrets["KRAKEN_API_KEY"],
        'secret': st.secrets["KRAKEN_SECRET"],
        'enableRateLimit': True,
    })

    # Récupération du solde réel
    balance = kraken.fetch_balance()
    usdc_reel = balance['total'].get('USDC', 0.0)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("SOLDE DISPO", f"{usdc_reel:.2f} USDC")

    # 3. PRIX LIVE
    ticker = kraken.fetch_ticker('XRP/USDC')
    prix_actuel = ticker['last']
    col2.metric("PRIX XRP", f"{prix_actuel:.4f} $")
    col3.metric("BOTS POSSIBLES", int(usdc_reel / 60)) # ~60$ par bot

    st.divider()

    # 4. CONFIGURATION DE TA FOURCHETTE (1.40 - 1.45)
    c1, c2, c3 = st.columns(3)
    p_min = c1.number_input("PRIX BAS", value=1.3500, format="%.4f")
    p_max = c2.number_input("PRIX HAUT", value=1.4500, format="%.4f")
    n_grids = c3.number_input("NBRE BOTS", value=50)

    # Volume par bot (3000$ / 50 = 60$ soit env 44 XRP)
    vol_per_bot = (usdc_reel * 0.98 / n_grids) / prix_actuel if usdc_reel > 10 else 44.0

    # 5. BOUTON DE DÉPLOIEMENT RÉEL
    if st.button("🚀 DÉPLOYER LA GRILLE SUR KRAKEN", type="primary", use_container_width=True):
        step = (p_max - p_min) / (n_grids - 1)
        prog = st.progress(0)
        
        for i in range(int(n_grids)):
            target_price = round(p_min + (i * step), 4)
            try:
                if target_price < prix_actuel:
                    # ACHAT RÉEL
                    kraken.create_limit_buy_order('XRP/USDC', vol_per_bot, target_price)
                else:
                    # VENTE RÉELLE
                    kraken.create_limit_sell_order('XRP/USDC', vol_per_bot, target_price)
                
                time.sleep(0.5) # Anti-blocage API
                prog.progress((i + 1) / n_grids)
            except Exception as e:
                st.error(f"Erreur palier {target_price}: {e}")
        
        st.balloons()
        st.success(f"✅ Grille de {n_grids} bots activée !")

except Exception as e:
    st.error(f"❌ Connexion impossible : {e}")
    st.info("Vérifie tes Secrets Streamlit : KRAKEN_API_KEY et KRAKEN_SECRET")

# Bouton de nettoyage
if st.button("🚨 ANNULER TOUS LES ORDRES"):
    kraken.cancel_all_orders('XRP/USDC')
    st.rerun()

time.sleep(20)
st.rerun()
