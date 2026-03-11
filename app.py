import streamlit as st
import ccxt
import json
import os
import time
from streamlit_autorefresh import st_autorefresh


# === CONFIGURATION ===
st.set_page_config(page_title="⚡ XRP Sniper Live (Finale protégée)", layout="centered")
symbol = "XRP/USDC"
st_autorefresh(interval=20000, key="refresh_app")
CONFIG_FILE = "bots_config.json"


# === ÉTAT / LOGS ===
if "logs" not in st.session_state: st.session_state.logs = []

def log(msg): 
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")


# === SAUVEGARDE / CHARGEMENT ROBUSTES ===
def save_bots():
    """Sauvegarde propre du fichier bots_config.json"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(st.session_state.bots, f, indent=2)
    except Exception as e:
        log(f"⚠️ Erreur sauvegarde JSON : {e}")

def load_bots():
    """Charge les bots, tolère un fichier JSON corrompu, recrée sinon."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    except json.JSONDecodeError:
        corrupt_name = f"corrupt_{int(time.time())}.json"
        os.rename(CONFIG_FILE, corrupt_name)
        log(f"⚠️ Fichier JSON corrompu renommé en {corrupt_name}. Réinitialisation.")
        return {}
    except Exception as e:
        log(f"⚠️ Erreur lecture JSON : {e}")
        return {}


# === CONNEXION KRAKEN ===
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True
    })
exchange = get_exchange()


# === INITIALISATION ===
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()
for b in st.session_state.bots.values():
    b.setdefault("actif", True)
    b.setdefault("etape", "ACHAT")
    b.setdefault("gain_net", 0.0)
    b.setdefault("cycles", 0)
save_bots()


# === PRIX LIVE ===
try:
    ticker = exchange.fetch_ticker(symbol)
    bid, ask, mid = ticker["bid"], ticker["ask"], (ticker["bid"] + ticker["ask"]) / 2
except Exception as e:
    bid = ask = mid = 0.0
    log(f"⚠️ Prix Kraken : {e}")

# === SOLDES ===
try:
    balances = exchange.fetch_balance()
    usdc = float(balances['free'].get('USDC', 0))
    xrp = float(balances['free'].get('XRP', 0))
except Exception:
    usdc = xrp = 0.0

# === PARAMÈTRES ===
st.sidebar.title("⚙️ Paramètres")
demo_mode = st.sidebar.toggle("💡 Mode Simulation (aucun ordre réel)", value=True)
st.sidebar.metric("Solde USDC", f"{usdc:.2f}$")
st.sidebar.metric("Solde XRP", f"{xrp:.2f}")

# === EN-TÊTE ===
st.title("🚀 XRP Sniper Live Trading (Version stable)")
st.metric("Prix moyen XRP", f"{mid:.5f}")
st.caption(f"Mise à jour : {time.strftime('%H:%M:%S')}")
st.divider()


# === AJOUT D’UN BOT ===
st.subheader("➕ Ajouter un bot")
col1,col2,col3 = st.columns(3)
with col1: p_achat_new = st.number_input("Prix Achat", value=1.390, step=0.0001)
with col2: p_vente_new = st.number_input("Prix Vente", value=1.400, step=0.0001)
with col3: mise_new = st.number_input("Mise ($)", value=10.0, step=1.0)

if st.button("✅ Ajouter ce bot"):
    next_id = max(st.session_state.bots.keys()) + 1 if st.session_state.bots else 1
    st.session_state.bots[next_id] = {
        "id": next_id, "p_achat": p_achat_new, "p_vente": p_vente_new,
        "mise": mise_new, "gain_net": 0.0, "cycles": 0,
        "actif": True, "etape": "ACHAT"
    }
    save_bots()
    log(f"🆕 Bot #{next_id} ajouté (Achat {p_achat_new:.4f} / Vente {p_vente_new:.4f})")
    st.success(f"Bot #{next_id} créé 🎯")
    st.rerun()


# === BOUCLE DE TRADING ===
for i,b in st.session_state.bots.items():
    if not b.get("actif"): continue
    try:
        qty_precision = exchange.market(symbol)['precision']['amount']
    except Exception:
        qty_precision = 4

    # --- ACHAT ---
    if b["etape"] == "ACHAT" and mid <= b["p_achat"]:
        if usdc >= b["mise"]:
            qty = round(b["mise"]/b["p_achat"], qty_precision)
            if demo_mode:
                log(f"🟡 [SIMU] Bot {i}: Achat {qty} XRP @ {b['p_achat']}")
            else:
                try:
                    exchange.create_limit_buy_order(symbol, qty, b["p_achat"])
                    log(f"✅ Bot {i}: Ordre d'achat envoyé ({qty} @ {b['p_achat']})")
                except Exception as e:
                    log(f"❌ Achat Bot {i}: {e}")
            b["etape"]="VENTE"
            save_bots()
        else:
            log(f"⚠️ Bot {i}: Solde USDC insuffisant ({usdc}$)")

    # --- VENTE ---
    elif b["etape"]=="VENTE" and mid >= b["p_vente"]:
        gain=(b["p_vente"]-b["p_achat"])/b["p_achat"]*b["mise"]
        if demo_mode:
            log(f"🔴 [SIMU] Bot {i}: Vente @ {b['p_vente']} (+{gain:.2f}$)")
        else:
            try:
                qty_sell = round(b["mise"]/b["p_achat"], qty_precision)
                exchange.create_limit_sell_order(symbol, qty_sell, b["p_vente"])
                log(f"💰 Bot {i}: Vente envoyée ({qty_sell} @ {b['p_vente']})")
            except Exception as e:
                log(f"❌ Vente Bot {i}: {e}")
        b["gain_net"]+=gain; b["cycles"]+=1; b["mise"]+=gain; b["etape"]="ACHAT"
        save_bots()


# === AFFICHAGE DES BOTS ===
st.divider()
st.subheader("📊 Mes bots")

if not st.session_state.bots:
    st.info("Aucun bot configuré.")
else:
    for i,b in sorted(st.session_state.bots.items()):
        couleur="⚫️" if not b["actif"] else "🟢"
        if b["actif"] and mid<=b["p_achat"]: couleur="🟡"
        elif b["actif"] and mid>=b["p_vente"]: couleur="🔴"
        st.info(
            f"{couleur} **Bot {i}** | Achat {b['p_achat']:.4f} | Vente {b['p_vente']:.4f} | "
            f"Mise :{b['mise']:.2f}$ | Gain :{b['gain_net']:.2f}$ | Cycles :{b['cycles']} | Étape :{b['etape']}"
        )


# === HISTORIQUE + PRIX DÉTAILLÉS ===
st.divider()
st.subheader("📜 Historique des tâches")
for line in reversed(st.session_state.logs[-15:]): st.write(line)

st.divider()
st.subheader("💹 Prix temps réel Kraken")
c1,c2,c3=st.columns(3)
c1.metric("Bid",f"{bid:.5f}")
c2.metric("Ask",f"{ask:.5f}")
c3.metric("Mid",f"{mid:.5f}")
