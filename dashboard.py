import streamlit as st
import krakenex
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURATION & STYLE
st.set_page_config(page_title="XRP Snowball Pro", layout="wide")
st.markdown("<style>.stMetric { background-color: #0e1117; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }</style>", unsafe_allow_html=True)

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# Initialisation de la mémoire du bot
if 'start_usdc' not in st.session_state: st.session_state.start_usdc = 0.0
if 'logs' not in st.session_state: st.session_state.logs = []

st.title("🛸 XRP SNOWBALL QUANTUM")

# 2. RÉCUPÉRATION DES DONNÉES LIVE
try:
    # Prix actuel
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})['result']['XRPUSDC']
    prix_actuel = float(ticker['c'][0])
    
    # Solde (29$ + dépôts)
    bal = k.query_private('Balance')['result']
    usdc_now = float(bal.get('USDC', 0))
    xrp_now = float(bal.get('XRP', 0))
    
    if st.session_state.start_usdc == 0: st.session_state.start_usdc = usdc_now
except:
    st.error("Erreur de connexion Kraken")
    prix_actuel, usdc_now, xrp_now = 0.0, 0.0, 0.0

# 3. DASHBOARD DE PERFORMANCE
c1, c2, c3, c4 = st.columns(4)
c1.metric("PRIX XRP", f"{prix_actuel:.4f} $")
c2.metric("SOLDE USDC", f"{usdc_now:.2f} $")
c3.metric("SOLDE XRP", f"{xrp_now:.2f}")
gain_total = usdc_now - st.session_state.start_usdc
c4.metric("PROFIT TOTAL", f"+{gain_total:.4f} $", delta=f"{((usdc_now/st.session_state.start_usdc)-1)*100:.2f}%" if st.session_state.start_usdc > 0 else "0%")

# 4. GRAPHIQUE DE NAVIGATION
# On simule une barre de progression entre l'achat et la vente
st.write("---")
st.subheader("🎯 Zone de Navigation")
p_achat = st.sidebar.number_input("Prix Achat", value=1.3600, format="%.4f")
p_vente = st.sidebar.number_input("Prix Vente", value=1.4000, format="%.4f")

# Visualisation simple
fig = go.Figure()
fig.add_trace(go.Scatter(x=[0, 1], y=[p_achat, p_achat], name="ACHAT", line=dict(color='cyan', dash='dash')))
fig.add_trace(go.Scatter(x=[0, 1], y=[p_vente, p_vente], name="VENTE", line=dict(color='lime', dash='dash')))
fig.add_trace(go.Scatter(x=[0.5], y=[prix_actuel], mode='markers+text', name="PRIX ACTUEL", 
                         text=[f"XRP: {prix_actuel}"], textposition="top center", marker=dict(size=20, color='white')))
fig.update_layout(height=200, showlegend=False, margin=dict(l=0,r=0,b=0,t=0), yaxis_range=[p_achat*0.98, p_vente*1.02])
st.plotly_chart(fig, use_container_width=True)

# 5. MOTEUR ET BOUTONS
if 'run' not in st.session_state: st.session_state.run = False
col_a, col_b = st.columns(2)

if col_a.button("▶️ ACTIVER LA BOUCLE", use_container_width=True, type="primary"):
    st.session_state.run = True
if col_b.button("⏹️ ARRÊTER / ANNULER", use_container_width=True):
    st.session_state.run = False
    k.query_private('CancelAll')
    st.rerun()

status = st.empty()
if st.session_state.run:
    try:
        ordres = k.query_private('OpenOrders').get('result', {}).get('open', {})
        if not ordres:
            # Calcul Snowball (Aspiration des 29$ + dépôts)
            vol_max = (usdc_now * 0.985) / p_achat
            if vol_max >= 10:
                params = {'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_achat), 'volume': str(round(vol_max, 1)),
                          'close[ordertype]': 'limit', 'close[price]': str(p_vente), 'close[type]': 'sell'}
                k.query_private('AddOrder', params)
                st.session_state.logs.append(f"✅ {datetime.now().strftime('%H:%M')} : Nouveau cycle lancé avec {vol_max:.2f} XRP")
            else:
                status.error("Solde insuffisant")
        else:
            for oid, det in ordres.items():
                status.info(f"🛰️ MISSION : {det['descr']['order']}")
    except Exception as e:
        st.error(f"API Error: {e}")
    
    time.sleep(15)
    st.rerun()

# 6. LOGS (Journal)
st.write("---")
with st.expander("📜 Journal des cycles", expanded=True):
    for log in reversed(st.session_state.logs):
        st.write(log)
