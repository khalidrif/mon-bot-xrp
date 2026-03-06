import streamlit as st
import krakenex
import time

# 1. STYLE PREMIUM (CSS CUSTOM)
st.set_page_config(page_title="XRP NEON COCKPIT", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Global Background */
    .stApp { background-color: #0E1117; }
    
    /* Cartes des Bots */
    .bot-card {
        border-radius: 15px;
        padding: 20px;
        background: linear-gradient(145deg, #1e2130, #161922);
        border: 1px solid #30363d;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    /* Metrics Style */
    [data-testid="stMetricValue"] {
        font-family: 'Courier New', monospace;
        font-weight: bold;
        color: #00f2ff !important;
    }
    
    /* Boutons custom */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s;
        border: 1px solid #30363d;
    }
    .stButton>button:hover {
        border-color: #00f2ff;
        box-shadow: 0 0 10px rgba(0,242,255,0.2);
    }
    
    /* Header Neon */
    .neon-text {
        text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff;
        color: #00f2ff;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONNEXION ---
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# --- FONCTION MÉMOIRE (USERREF) ---
def encode_ref(p_in, p_out):
    return int((p_in * 1000) * 1000 + (min(p_out/p_in, 2.0) * 1000))

def decode_ref(ref):
    p_in = (ref // 1000) / 1000
    ratio = (ref % 1000) / 1000
    return p_in, p_in * ratio

# --- DATA ---
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(ticker['result']['XRPUSDC']['c'][0])
    res_open = k.query_private('OpenOrders')
    ordres = res_open.get('result', {}).get('open', {})
except:
    prix_actuel, ordres = 0.0, {}

# --- LAYOUT TOP ---
st.markdown("<h1 class='neon-text'>🛸 XRP NEON COCKPIT v2</h1>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    st.metric("XRP / USDC", f"{prix_actuel:.4f} $", delta=f"{0.02:.2f}%")
with c2:
    st.metric("BOTS ACTIFS", len(ordres))
with c3:
    if st.button("🚨 EMERGENCY STOP", type="primary", use_container_width=True):
        k.query_private('CancelAll')
        st.rerun()

st.write("")

# --- FORMULAIRE DESIGN ---
with st.container():
    st.markdown("<div style='background:#161922; padding:20px; border-radius:15px; border:1px solid #00f2ff33'>", unsafe_allow_html=True)
    col_a, col_b, col_c, col_d = st.columns(4)
    p_in = col_a.number_input("PRIX ACHAT", value=round(prix_actuel*0.995, 4), format="%.4f")
    p_out = col_b.number_input("PRIX VENTE", value=round(p_in*1.02, 4), format="%.4f")
    vol = col_c.number_input("VOLUME XRP", value=20.0)
    
    if col_d.button("🚀 LANCER LE BOT", use_container_width=True):
        memo = encode_ref(p_in, p_out)
        k.query_private('AddOrder', {
            'pair': 'XRPUSDC', 'type': 'buy', 'ordertype': 'limit', 'price': str(round(p_in, 4)), 
            'volume': str(vol), 'userref': str(memo),
            'close[ordertype]': 'limit', 'close[price]': str(round(p_out, 4)), 'close[type]': 'sell'
        })
        st.balloons()
        time.sleep(1)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# --- GRID DES BOTS ---
if ordres:
    cols = st.columns(3)
    for i, (oid, det) in enumerate(ordres.items()):
        with cols[i % 3]:
            type_o = det['descr']['type'].upper()
            prix_o = float(det['descr']['price'])
            p_in_m, p_out_m = decode_ref(int(det.get('userref', 0)))
            
            # Couleur dynamique
            color = "#00ff88" if type_o == "BUY" else "#ff4b4b"
            label = "ACHAT" if type_o == "BUY" else "VENTE"
            
            st.markdown(f"""
                <div class="bot-card">
                    <h3 style="color:{color}; margin-top:0;">🤖 BOT {i+1} <span style="font-size:12px; color:#666;">ID: {oid[:5]}</span></h3>
                    <div style="display:flex; justify-content:space-between;">
                        <span>Cible {label} :</span>
                        <b style="color:{color}">{prix_o:.4f}</b>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                        <span>Volume :</span>
                        <b>{det['vol']} XRP</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"ARRÊTER BOT {i+1}", key=oid, use_container_width=True):
                k.query_private('CancelOrder', {'txid': oid})
                st.rerun()
else:
    st.markdown("<div style='text-align:center; padding:50px; color:#666;'>Aucune mission en cours...</div>", unsafe_allow_html=True)

# Auto-refresh
time.sleep(15)
st.rerun()
