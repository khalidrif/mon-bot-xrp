import streamlit as st
import ccxt
import json
import os
import time
from streamlit_autorefresh import st_autorefresh


# === CONFIGURATION ===
st.set_page_config(page_title="⚡ XRP Sniper Pro (Portefeuille Total)", layout="centered")
symbol = "XRP/USDC"
CONFIG_FILE = "bots_config.json"
st_autorefresh(interval=20000, key="refresh_app")  # rafraîchit toutes les 20 s


# === LOGS ===
if "logs" not in st.session_state:
    st.session_state.logs = []
def log(msg): st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")


# === SAUVEGARDE / CHARGEMENT ROBUSTE ===
def save_bots():
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(st.session_state.bots, f, indent=2)
    except Exception as e:
        log(f"⚠️ Erreur sauvegarde JSON : {e}")

def load_bots():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    except json.JSONDecodeError:
        backup = f"corrupt_{int(time.time())}.json"
        os.rename(CONFIG_FILE, backup)
        log(f"⚠️ JSON corrompu renommé : {backup}")
        return {}
    except Exception as e:
        log(f"⚠️ Erreur lecture JSON : {e}")
        return {}


# === CONNEXION KRAKEN ===
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"],
        "secret": st.secrets["KRAKEN_API_SECRET"],
        "enableRateLimit": True
    })
exchange = get_exchange()


# === INITIALISATION DES BOTS ===
if "bots" not in st.session_state:
    st.session_state.bots = load_bots()
for b in st.session_state.bots.values():
    b.setdefault("actif", True)
    b.setdefault("etape", "ACHAT")
    b.setdefault("gain_net", 0.0)
    b.setdefault("cycles", 0)
save_bots()


# === PRIX LIVE ET SOLDES ===
try:
    ticker = exchange.fetch_ticker(symbol)
    bid, ask = ticker["bid"], ticker["ask"]
    mid = (bid + ask) / 2
except Exception as e:
    bid = ask = mid = 0.0
    log(f"⚠️ Erreur prix Kraken : {e}")

# Soldes du compte
try:
    balances = exchange.fetch_balance()
    usdc = float(balances["free"].get("USDC", 0))
    xrp = float(balances["free"].get("XRP", 0))
except Exception:
    usdc = xrp = 0.0

# Ajoute la valeur des ordres ouverts (si présents)
try:
    open_orders = exchange.fetch_open_orders(symbol)
    xrp_open = sum(float(o["amount"]) for o in open_orders if o.get("side") == "sell")
    usdc_open = sum(float(o["price"]) * float(o["amount"]) for o in open_orders if o.get("side") == "buy")
except Exception:
    xrp_open = 0.0
    usdc_open = 0.0

# Valeur totale du portefeuille = XRP*mid + USDC + valeurs ouvertes
wallet_total = usdc + usdc_open + (xrp + xrp_open) * mid


# === EN‑TÊTE ===
st.title("🚀 XRP Sniper Pro – Portefeuille live Kraken")
col1, col2, col3, col4 = st.columns(4)
col1.metric("💵 USDC libres", f"{usdc:.2f}$")
col2.metric("💠 XRP libres", f"{xrp:.2f}")
col3.metric("📊 Valeurs en ordres", f"{(usdc_open + xrp_open * mid):.2f}$")
col4.metric("💰 Valeur totale (en USDC)", f"{wallet_total:.2f}$")
st.caption(f"Prix XRP {mid:.5f} | Dernière mise à jour : {time.strftime('%H:%M:%S')}")
st.divider()


# === AJOUT D’UN BOT ===
st.subheader("➕ Ajouter un bot")
c1, c2, c3 = st.columns(3)
with c1:
    p_achat_new = st.number_input("Prix Achat", value=1.00000, step=0.00001, format="%.5f")
with c2:
    p_vente_new = st.number_input("Prix Vente", value=1.00000, step=0.00001, format="%.5f")
with c3:
    mise_new = st.number_input("Mise ($)", value=10.0, step=0.1, format="%.2f")

if st.button("✅ Créer le bot"):
    next_id = max(st.session_state.bots.keys()) + 1 if st.session_state.bots else 1
    st.session_state.bots[next_id] = {
        "id": next_id, "p_achat": p_achat_new, "p_vente": p_vente_new,
        "mise": mise_new, "gain_net": 0.0, "cycles": 0,
        "actif": True, "etape": "ACHAT"
    }
    save_bots()
    log(f"🆕 Bot #{next_id} Achat {p_achat_new:.5f} / Vente {p_vente_new:.5f}")
    st.success(f"Bot #{next_id} créé ✅")
    st.rerun()


# === LOGIQUE TRADING ===
for i, b in st.session_state.bots.items():
    if not b.get("actif"): 
        continue
    try:
        market = exchange.market(symbol)
        prec = market.get("precision", {}).get("amount", 4)
        qty_precision = int(prec) if isinstance(prec, (int, float)) else 4
    except Exception:
        qty_precision = 4

    # Étape achat
    if b["etape"] == "ACHAT" and mid <= b["p_achat"]:
        if usdc >= b["mise"]:
            qty = round(b["mise"] / b["p_achat"], qty_precision)
            try:
                exchange.create_limit_buy_order(symbol, qty, b["p_achat"])
                log(f"✅ Bot {i} : Achat réel {qty} XRP @ {b['p_achat']:.5f}")
                b["etape"] = "VENTE"
                save_bots()
            except Exception as e:
                log(f"❌ Achat Bot {i} : {e}")
        else:
            log(f"⚠️ Bot {i} : Solde USDC insuffisant ({usdc}$)")

    # Étape vente
        # === Étape vente (VERSION SÉCURISÉE ET CORRIGÉE) ===
    elif b["etape"] == "VENTE" and mid >= b["p_vente"]:
        # 1. On prépare les chiffres
        gain = (b["p_vente"] - b["p_achat"]) / b["p_achat"] * b["mise"]
        qty_sell = round(b["mise"] / b["p_achat"], qty_precision)

        # 2. LE VERROU : On change l'étape TOUT DE SUITE pour bloquer les doublons
        b["etape"] = "EN_COURS" 
        save_bots()

        try:
            # 3. On envoie l'ordre à Kraken
            exchange.create_limit_sell_order(symbol, qty_sell, b["p_vente"])
            log(f"💰 Bot {i} : Vente réelle @ {b['p_vente']:.5f} (+{gain:.2f}$)")
            
            # 4. ON NE CALCULE LES GAINS QUE SI L'ORDRE A RÉUSSI
            b["gain_net"] += gain
            b["cycles"] += 1
            b["mise"] += gain
            b["etape"] = "ACHAT" # On autorise le prochain achat
            save_bots()
            
        except Exception as e:
            log(f"❌ Erreur Vente Bot {i} : {e}")
            # SI ÇA ÉCHOUE : On remet l'étape en "VENTE" pour réessayer au prochain tour
            b["etape"] = "VENTE"
            save_bots()



# === TOTAL DES GAINS ===
total_gain = sum(b["gain_net"] for b in st.session_state.bots.values())
st.success(f"💰 Gains cumulés de tous les bots : {total_gain:.2f}$")
st.divider()


# === AFFICHAGE DES BOTS ===
st.subheader("📊 Mes bots actifs")
if not st.session_state.bots:
    st.info("Aucun bot configuré.")
else:
    for i, b in sorted(st.session_state.bots.items()):
        actif = b.get("actif", True)
        couleur = "⚫️" if not actif else "🟢"
        if actif and mid <= b["p_achat"]: couleur = "🟡"
        elif actif and mid >= b["p_vente"]: couleur = "🔴"

        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.info(
                f"{couleur} **Bot {i}** | Achat {b['p_achat']:.5f} | Vente {b['p_vente']:.5f} | "
                f"Mise :{b['mise']:.2f}$ | Gain :{b['gain_net']:.2f}$ | Cycles :{b['cycles']} | Étape :{b['etape']}"
            )
        with col2:
            toggle = "🛑" if actif else "🚀"
            if st.button(toggle, key=f"toggle_{i}"):
                b["actif"] = not actif
                save_bots()
                log(f"🔁 Bot #{i} {'désactivé' if actif else 'activé'}.")
                st.rerun()
        with col3:
            if st.button("🗑️", key=f"del_{i}"):
                del st.session_state.bots[i]
                save_bots()
                log(f"🗑️ Bot #{i} supprimé.")
                st.rerun()


# === JOURNAL + PRIX ===
st.divider()
st.subheader("📜 Journal complet")
if st.session_state.logs:
    st.text_area("Derniers évènements", "\n".join(reversed(st.session_state.logs[-200:])), height=220)
else:
    st.info("Aucune activité pour le moment.")

st.divider()
st.subheader("💹 Prix en temps réel Kraken")
c1,c2,c3=st.columns(3)
c1.metric("Bid", f"{bid:.5f}")
c2.metric("Ask", f"{ask:.5f}")
c3.metric("Mid", f"{mid:.5f}")

