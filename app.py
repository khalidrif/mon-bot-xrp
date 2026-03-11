import streamlit as st
import ccxt
import json
import os
import time
from streamlit_autorefresh import st_autorefresh


# === CONFIGURATION ===
st.set_page_config(page_title="⚡ XRP Sniper Pro (Finale)", layout="centered")
symbol = "XRP/USDC"
st_autorefresh(interval=20000, key="refresh_app")  # rafraîchissement toutes les 20s
CONFIG_FILE = "bots_config.json"


# === SESSION / LOGS ===
if "logs" not in st.session_state:
    st.session_state.logs = []

def log(msg):
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")


# === SAUVEGARDE / CHARGEMENT ROBUSTE ===
def save_bots():
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(st.session_state.bots, f, indent=2)
    except Exception as e:
        log(f"⚠️ Erreur sauvegarde JSON : {e}")

def load_bots():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    except json.JSONDecodeError:
        corrupt = f"corrupt_{int(time.time())}.json"
        os.rename(CONFIG_FILE, corrupt)
        log(f"⚠️ Fichier JSON corrompu renommé : {corrupt}")
        return {}
    except Exception as e:
        log(f"⚠️ Erreur lecture JSON : {e}")
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

# === INITIALISATION DES BOTS ===
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

for b in st.session_state.bots.values():
    b.setdefault("actif", True)
    b.setdefault("etape", "ACHAT")
    b.setdefault("gain_net", 0.0)
    b.setdefault("cycles", 0)

save_bots()


# === PRIX ET SOLDES ===
try:
    ticker = exchange.fetch_ticker(symbol)
    bid, ask = ticker["bid"], ticker["ask"]
    mid = (bid + ask) / 2
except Exception as e:
    bid = ask = mid = 0.0
    log(f"⚠️ Prix Kraken : {e}")

try:
    balances = exchange.fetch_balance()
    usdc = float(balances['free'].get('USDC', 0))
    xrp = float(balances['free'].get('XRP', 0))
except Exception:
    usdc = xrp = 0.0


# === PARAMÈTRES SIDEBAR ===
st.sidebar.title("⚙️ Paramètres")
demo_mode = st.sidebar.toggle("💡 Mode Simulation (pas d’ordre réel)", value=True)
st.sidebar.metric("Solde USDC", f"{usdc:.2f}$")
st.sidebar.metric("Solde XRP", f"{xrp:.2f}")


# === EN‑TÊTE ===
st.title("🚀 XRP Sniper Pro (Full Version)")
st.metric("Prix moyen XRP", f"{mid:.5f}")
st.caption(f"Mise à jour : {time.strftime('%H:%M:%S')}")
st.divider()


# === AJOUT D’UN BOT ===
st.subheader("➕ Ajouter un bot")
c1, c2, c3 = st.columns(3)
with c1: p_achat_new = st.number_input("Prix d’Achat", value=1.390, step=0.0001)
with c2: p_vente_new = st.number_input("Prix de Vente", value=1.400, step=0.0001)
with c3: mise_new = st.number_input("Mise ($)", value=10.0, step=1.0)

if st.button("✅ Créer le bot"):
    next_id = max(st.session_state.bots.keys()) + 1 if st.session_state.bots else 1
    st.session_state.bots[next_id] = {
        "id": next_id,
        "p_achat": p_achat_new,
        "p_vente": p_vente_new,
        "mise": mise_new,
        "gain_net": 0.0,
        "cycles": 0,
        "actif": True,
        "etape": "ACHAT"
    }
    save_bots()
    log(f"🆕 Bot #{next_id} ajouté (Achat {p_achat_new:.4f} / Vente {p_vente_new:.4f})")
    st.rerun()


# === BOUCLE DE TRADING ===
for i, b in st.session_state.bots.items():
    if not b.get("actif"):  # bot désactivé
        continue
    try:
        market = exchange.market(symbol)
        prec = market.get("precision", {}).get("amount", 4)
        qty_precision = int(prec) if isinstance(prec, (int, float)) else 4
    except Exception:
        qty_precision = 4

    # --- Étape ACHAT ---
    if b["etape"] == "ACHAT" and mid <= b["p_achat"]:
        if usdc >= b["mise"]:
            qty = round(b["mise"] / b["p_achat"], qty_precision)
            if demo_mode:
                log(f"🟡 [SIMU] Bot {i}: Achat virtuel {qty} XRP @ {b['p_achat']}")
            else:
                try:
                    exchange.create_limit_buy_order(symbol, qty, b["p_achat"])
                    log(f"✅ Bot {i}: Achat réel {qty} @ {b['p_achat']}")
                except Exception as e:
                    log(f"❌ Erreur achat #{i} : {e}")
            b["etape"] = "VENTE"
            save_bots()
        else:
            log(f"⚠️ Bot {i}: Solde USDC insuffisant ({usdc}$)")

    # --- Étape VENTE ---
    elif b["etape"] == "VENTE" and mid >= b["p_vente"]:
        gain = (b["p_vente"] - b["p_achat"]) / b["p_achat"] * b["mise"]
        if demo_mode:
            log(f"🔴 [SIMU] Bot {i}: Vente virt. @ {b['p_vente']} (+{gain:.2f}$)")
        else:
            try:
                qty_sell = round(b["mise"] / b["p_achat"], qty_precision)
                exchange.create_limit_sell_order(symbol, qty_sell, b["p_vente"])
                log(f"💰 Bot {i}: Vente réelle @ {b['p_vente']}")
            except Exception as e:
                log(f"❌ Erreur vente #{i}: {e}")
        b["gain_net"] += gain
        b["cycles"] += 1
        b["mise"] += gain  # effet boule de neige
        b["etape"] = "ACHAT"
        save_bots()


# === AFFICHAGE DES BOTS ===
st.divider()
st.subheader("📊 Mes Bots")

if not st.session_state.bots:
    st.info("Aucun bot configuré.")
else:
    for i, b in sorted(st.session_state.bots.items()):
        actif = b.get("actif", True)
        couleur = "⚫️" if not actif else "🟢"
        if actif and mid <= b["p_achat"]: couleur = "🟡"
        elif actif and mid >= b["p_vente"]: couleur = "🔴"

        c1, c2, c3 = st.columns([4, 1, 1])
        with c1:
            st.info(
                f"{couleur} **Bot {i}** | Achat {b['p_achat']:.4f} | Vente {b['p_vente']:.4f} | "
                f"Mise :{b['mise']:.2f}$ | Gain :{b['gain_net']:.2f}$ | Cycles :{b['cycles']} | Étape :{b['etape']}"
            )
        with c2:
            toggle = "🛑" if actif else "🚀"
            if st.button(toggle, key=f"toggle_{i}"):
                b["actif"] = not actif
                save_bots()
                log(f"🔁 Bot #{i} {'désactivé' if actif else 'activé'}.")
                st.rerun()
        with c3:
            if st.button("🗑️", key=f"del_{i}"):
                del st.session_state.bots[i]
                save_bots()
                log(f"🗑️ Bot #{i} supprimé.")
                st.rerun()


# === LOGS + PRIX LIVE ===
st.divider()
st.subheader("📜 Historique des tâches récentes")
for line in reversed(st.session_state.logs[-15:]):
    st.write(line)

st.divider()
st.subheader("💹 Prix temps réel Kraken")
c1,c2,c3 = st.columns(3)
c1.metric("Bid", f"{bid:.5f}")
c2.metric("Ask", f"{ask:.5f}")
c3.metric("Mid", f"{mid:.5f}")
