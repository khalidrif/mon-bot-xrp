import streamlit as st
import krakenex
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Cockpit Pro", layout="wide")

# Injection de style CSS
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ffcc; }
    .stButton>button { border-radius: 8px; height: 3em; font-weight: bold; }
    .bot-card { border: 1px solid #444; padding: 15px; border-radius: 10px; background: #1e1e1e; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNEXION API ---
# Note : Assure-toi que tes secrets sont bien configurés dans .streamlit/secrets.toml
k = krakenex.API(key=st.secrets["KRAKEN_KEY"], secret=st.secrets["KRAKEN_SECRET"])

# --- FONCTION MÉMOIRE (USERREF) ---
# Kraken limite userref à un entier 32-bit (max 2.1 milliards)
# On stocke : (PrixAchat * 1000) et l'écart en % (multiplié par 100)
def encode_ref(p_in, p_out):
    return int((p_in * 1000) * 1000 + ((p_out/p_in - 1) * 10000))

def decode_ref(ref):
    p_in = (ref // 1000) / 1000
    profit_pct = (ref % 1000) / 10000
    p_out = p_in * (1 + profit_pct)
    return p_in, p_out

# --- SIDEBAR & ACTIONS GLOBALES ---
with st.sidebar:
    st.title("⚙️ Contrôle")
    if st.button("🗑️ ANNULER TOUS LES ORDRES", type="primary"):
        k.query_private('CancelAll')
        st.success("Signal d'annulation envoyé")
        time.sleep(1)
        st.rerun()
    
    st.write("---")
    st.caption("Auto-refresh : 30s")

# --- RÉCUPÉRATION DONNÉES ---
try:
    ticker = k.query_public('Ticker', {'pair': 'XRPUSDC'})
    prix_actuel = float(ticker['result']['XRPUSDC']['c'][0])
    
    res_open = k.query_private('OpenOrders')
    ordres = res_open.get('result', {}).get('open', {})
except Exception as e:
    st.error(f"Erreur API : {e}")
    prix_actuel = 0.0
    ordres = {}

# --- HEADER ---
c_head1, c_head2 = st.columns([2, 1])
with c_head1:
    st.title("🕹️ Cockpit Multi-Bots XRP")
with c_head2:
    st.metric("PRIX ACTUEL XRP", f"{prix_actuel:.4f} USDC", delta_color="normal")

# --- FORMULAIRE DE LANCEMENT ---
with st.expander("🚀 CONFIGURER UN NOUVEAU BOT", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    p_in = c1.number_input("PRIX ACHAT (Limite)", value=round(prix_actuel*0.99, 4), format="%.4f")
    p_out = c2.number_input("PRIX VENTE (Take Profit)", value=round(p_in*1.05, 4), format="%.4f")
    vol = c3.number_input("QUANTITÉ (XRP)", value=15.0, step=1.0)
    
    if c4.button("⚡ ACTIVER LE BOT", use_container_width=True):
        memo = encode_ref(p_in, p_out)
        order_params = {
            'pair': 'XRPUSDC',
            'type': 'buy',
            'ordertype': 'limit',
            'price': str(round(p_in, 4)),
            'volume': str(vol),
            'userref': str(memo),
            'close[ordertype]': 'limit',
            'close[price]': str(round(p_out, 4)),
            'close[type]': 'sell'
        }
        res = k.query_private('AddOrder', order_params)
        if res.get('error'):
            st.error(f"Refus Kraken : {res['error']}")
        else:
            st.balloons()
            time.sleep(1)
            st.rerun()

st.write("---")

# --- AFFICHAGE DES BOTS ACTIFS ---
if ordres:
    st.subheader(f"🤖 Bots en cours ({len(ordres)})")
    cols = st.columns(3)
    
    for i, (oid, det) in enumerate(ordres.items()):
        with cols[i % 3]:
            # Parsing des infos
            type_o = det['descr']['type'].upper()
            prix_o = float(det['descr']['price'])
            vol_o = float(det['vol'])
            
            # Décodage mémoire
            try:
                p_in_m, p_out_m = decode_ref(int(det.get('userref', 0)))
            except:
                p_in_m, p_out_m = 0.0, 0.0

            # Card UI
            with st.container():
                if type_o == "BUY":
                    st.markdown(f"### 🟢 BOT #{i+1}")
                    st.write(f"**Statut :** Attente Achat")
                    st.write(f"**Cible :** `{prix_o:.4f}`")
                    st.progress(min(max(1 - (prix_o/prix_actuel - 1), 0.0), 1.0) if prix_actuel > 0 else 0)
                else:
                    st.markdown(f"### 🔴 BOT #{i+1}")
                    st.write(f"**Statut :** En vente (Profit!)")
                    st.write(f"**Cible :** `{prix_o:.4f}`")
                    if p_in_m > 0:
                        profit = (prix_o / p_in_m - 1) * 100
                        st.info(f"Profit visé : +{profit:.2f}%")

                if st.button(f"STOP & ANNULER", key=oid):
                    k.query_private('CancelOrder', {'txid': oid})
                    st.rerun()
else:
    st.info("Aucun bot actif. Configurez un prix d'achat ci-dessus.")

# Auto-refresh simple (toutes les 30 sec)
time.sleep(30)
st.rerun()
