import streamlit as st
import krakenex
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. STYLE & SETUP
st.set_page_config(page_title="XRP SNOWBALL V3", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS pour un look "Neon & Dark"
st.markdown("""
    <style>
    .stApp { background-color: #050a12; }
    [data-testid="stMetricValue"] { font-family: 'Courier New', monospace; color: #00f2ff !important; font-size: 2rem !important; }
    .stMetric { background: #0b1423; border: 1px solid #1a2a40; padding: 15px; border-radius: 12px; }
    .status-card { background: #161922; border-left: 5px solid #00f2ff; padding: 20px; border-radius: 8px; margin: 10px 0; }
    .stButton>button { border-radius: 20px; font-weight: bold; transition: 0.3s; }
    </style>
    """, unsafe_allow_html=True)

k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# Initialisation
if 'logs' not in st.session_state: st.session_state.logs = []
if 'start_val' not in st.session_state: st.session_state.start_val = 0.0

# 2. DATA FETCHING
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})['result']['XRPUSDC']
    prix_actuel = float(ticker['c'][0])
    
    bal = k.query_private('Balance')['result']
    usdc = float(bal.get('USDC', 0))
    xrp = float(bal.get('XRP', 0))
    
    if st.session_state.start_val == 0: st.session_state.start_val = usdc
except:
    prix_actuel, usdc, xrp = 0.0, 0.0, 0.0

# 3. HEADER & METRICS
st.markdown("<h1 style='text-align: center; color: #00f2ff; text-shadow: 0 0 10px #00f2ff;'>🛸 XRP QUANTUM SNOWBALL</h1>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("PRIX LIVE", f"{prix_actuel:.4f} $")
m2.metric("SOLDE USDC", f"{usdc:.2f} $")
m3.metric("SOLDE XRP", f"{xrp:.2f}")
gain = usdc - st.session_state.start_val
m4.metric("PROFIT NET", f"+{gain:.4f} $", delta=f"{((usdc/st.session_state.start_val)-1)*100:.2f}%" if st.session_state.start_val > 0 else "0%")

st.write("---")

# 4. GRAPHIQUE RADAR (PROXIMITÉ CIBLES)
c_left, c_right = st.columns([1, 2])

with c_left:
    st.subheader("🎯 Configuration")
    p_in = st.number_input("ACHAT (Bas)", value=1.3600, format="%.4f", step=0.0001)
    p_out = st.number_input("VENTE (Haut)", value=1.4000, format="%.4f", step=0.0001)
    
    # Boutons Design
    if 'run' not in st.session_state: st.session_state.run = False
    if st.button("🚀 LANCER LA BOUCLE", use_container_width=True, type="primary", disabled=st.session_state.run):
        st.session_state.run = True
    if st.button("⏹️ STOP & RESET", use_container_width=True):
        st.session_state.run = False
        k.query_private('CancelAll')
        st.rerun()

with c_right:
    # Visualisation du prix entre les bornes
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=p_in, x1=1, y1=p_out, fillcolor="rgba(0,242,255,0.05)", line_width=0)
    fig.add_trace(go.Scatter(x=[0, 1], y=[p_in, p_in], name="ACHAT", line=dict(color="#ff3366", width=2, dash='dot')))
    fig.add_trace(go.Scatter(x=[0, 1], y=[p_out, p_out], name="VENTE", line=dict(color="#00ffcc", width=2, dash='dot')))
    fig.add_trace(go.Scatter(x=[0.5], y=[prix_actuel], mode="markers+text", text=["XRP LIVE"], textposition="top center", marker=dict(size=18, color="white", line=dict(width=2, color="#00f2ff"))))
    fig.update_layout(height=250, margin=dict(l=20,r=20,b=20,t=20), showlegend=False, template="plotly_dark", yaxis_range=[p_in*0.98, p_out*1.02])
    st.plotly_chart(fig, use_container_width=True)

# 5. LOGIQUE & STATUS
status_box = st.empty()

if st.session_state.run:
    try:
        res = k.query_private('OpenOrders').get('result', {}).get('open', {})
        if not res:
            # Calcul automatique Boule de Neige
            vol = (usdc * 0.985) / p_in
            if vol >= 10:
                params = {'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(p_in), 'volume': str(round(vol, 1)),
                          'close[ordertype]': 'limit', 'close[price]': str(p_out), 'close[type]': 'sell'}
                k.query_private('AddOrder', params)
                st.session_state.logs.append(f"✅ {datetime.now().strftime('%H:%M')} : Nouveau cycle avec {vol:.1f} XRP")
            else:
                status_box.error("Solde USDC trop faible pour le minimum Kraken (10 XRP).")
        else:
            for oid, det in res.items():
                status_box.markdown(f"<div class='status-card'>📡 <b>MISSION EN COURS :</b> {det['descr']['order']}</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"API Error: {e}")
    
    time.sleep(15)
    st.rerun()

# 6. HISTORIQUE
st.write("---")
with st.expander("📜 Journal des cycles validés", expanded=True):
    if st.session_state.logs:
        for log in reversed(st.session_state.logs):
            st.write(log)
    else:
        st.caption("En attente du premier cycle...")
