import streamlit as st
import ccxt
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="XRP SNIPER AUTO-OFF (sécurisé)", layout="wide")
symbol = "XRP/USDC"
st_autorefresh(interval=40000, key="bot_refresh")  # rafraîchit toutes les 40s

# --- 2. INITIALISATION SESSION ---
if "logs" not in st.session_state: st.session_state.logs = []
if "run" not in st.session_state: st.session_state.run = True
if "global_lock" not in st.session_state: st.session_state.global_lock = False

def log(msg): 
    st.session_state.logs.append(f"{time.strftime('%H:%M:%S')} | {msg}")

# --- 3. CONNEXION EXCHANGE (KRAKEN) ---
@st.cache_resource
def get_exchange():
    return ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_API_KEY"], 
        "secret": st.secrets["KRAKEN_API_SECRET"], 
        "enableRateLimit": True
    })

exchange = get_exchange()

# --- 4. PARAMÈTRES DES BOTS ---
if "bots" not in st.session_state:
    st.session_state.bots = {
        1: {"id": 1, "actif": True, "p_achat": 1.400, "p_vente": 1.410, "mise": 15.0, 
            "etape": "ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0, "last_action_time": 0},
        2: {"id": 2, "actif": True, "p_achat": 1.396, "p_vente": 1.400, "mise": 15.0,
            "etape": "ACHAT", "qty": 0.0, "gain_cumule": 0.0, "cycles": 0, "last_action_time": 0}
    }


# --- 5. BOUCLE DE TRADING SÉCURISÉE ---
def run_cycle():
    if st.session_state.global_lock:
        log("⛔️ Cycle bloqué (verrou global actif).")
        return

    # Récupération données Kraken
    try:
        ticker = exchange.fetch_ticker(symbol, params={'nonce': str(int(time.time()*1000))})
        price = float((ticker["bid"] + ticker["ask"]) / 2)
        st.session_state.price = price
        bal = exchange.fetch_balance()
        st.session_state.usdc = float(bal['free'].get('USDC', 0.0))
        st.session_state.xrp = float(bal['free'].get('XRP', 0.0))
        log(f"🎯 Flux : {price:.5f} | USDC dispo : {st.session_state.usdc:.2f}$")
    except Exception as e:
        log(f"⚠️ Erreur fetching ticker/balance : {e}")
        return

    if not st.session_state.run:
        return

    now = time.time()

    for i in sorted(st.session_state.bots.keys()):
        bot = st.session_state.bots[i]
        if not bot.get("actif"):
            continue

        # Protection anti-double clic / double cycle
        if now - bot.get("last_action_time", 0) < 10:
            log(f"⏸ Bot {i} : action ignorée (trop récente).")
            continue

        mise_actu = bot["mise"] + bot["gain_cumule"]

        # --- LOGIQUE D'ACHAT ---
        if bot["etape"] == "ACHAT" and st.session_state.price <= bot["p_achat"]:
            if st.session_state.usdc >= mise_actu and not st.session_state.global_lock:
                st.session_state.global_lock = True
                bot["actif"] = False
                try:
                    p_target = bot["p_achat"]
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / p_target))
                    exchange.create_limit_buy_order(symbol, qty, p_target)
                    bot.update({
                        "qty": qty,
                        "etape": "VENTE",
                        "last_action_time": now
                    })
                    log(f"✅ Bot {i} : LIMIT ACHAT à {p_target}. Désactivé (safe mode).")
                except Exception as e:
                    bot["actif"] = True
                    log(f"❌ Erreur Achat Bot {i} : {e}")
                finally:
                    st.session_state.global_lock = False
                break

        # --- LOGIQUE DE VENTE ---
        elif bot["etape"] == "VENTE" and st.session_state.price >= bot["p_vente"]:
            if bot.get("qty", 0) > 0 and not st.session_state.global_lock:
                st.session_state.global_lock = True
                bot["actif"] = False
                try:
                    p_target = bot["p_vente"]
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    exchange.create_limit_sell_order(symbol, qty_sell, p_target)
                    gain = (p_target * qty_sell) - mise_actu
                    bot.update({
                        "gain_cumule": bot["gain_cumule"] + gain,
                        "cycles": bot["cycles"] + 1,
                        "qty": 0.0,
                        "etape": "ACHAT",
                        "last_action_time": now
                    })
                    log(f"💰 Bot {i} : LIMIT VENTE à {p_target}. Désactivé (safe mode).")
                except Exception as e:
                    bot["actif"] = True
                    log(f"❌ Erreur Vente Bot {i} : {e}")
                finally:
                    st.session_state.global_lock = False
                break

    log("🕒 Cycle terminé - attente du prochain refresh.")


# --- 6. DÉCLENCHEMENT DU CYCLE ---
run_cycle()


# --- 7. INTERFACE UTILISATEUR ---
st.title("🚀 XRP SNIPER AUTO-OFF (sécurisé)")
st.caption(f"Dernière mise à jour : {time.strftime('%H:%M:%S')}")

m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price', 0):.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc', 0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp', 0):.2f}")

st.divider()

# TABLEAU DE CONTRÔLE DES BOTS
cols_header = st.columns([0.4,0.4,0.7,0.7,0.8,0.8,0.6,1.4,0.5,0.6])
labels = ["ID","St","Achat","Vente","Mise","Gain","Qty","Étape","Cy","Go"]
for c, lbl in zip(cols_header, labels): c.write(f"**{lbl}**")

for i in sorted(st.session_state.bots.keys()):
    bt = st.session_state.bots[i]
    r = st.columns([0.4,0.4,0.7,0.7,0.8,0.8,0.6,1.4,0.5,0.6])
    r[0].write(f"#{i}")
    r[1].write("✅" if bt["actif"] else "⚪")
    r[2].write(f"{bt['p_achat']:.3f}")
    r[3].write(f"{bt['p_vente']:.3f}")
    r[4].write(f"{bt['mise'] + bt['gain_cumule']:.1f}$")
    g = bt["gain_cumule"]
    r[5].markdown(f"**:green[+{g:.2f}$]**" if g > 0 else f"{g:.2f}$")
    r[6].write(f"{bt['qty']:.2f}")
    if bt["etape"] == "ACHAT": r[7].markdown("🟢 **ACHAT**")
    else: r[7].markdown("🟠 **VENTE**")
    r[8].write(str(bt["cycles"]))
    if r[9].button("🚀" if not bt["actif"] else "🛑", key=f"btn{i}"):
        st.session_state.bots[i]["actif"] = not bt["actif"]
        log(f"🔁 Bot {i} : état modifié -> {'ON' if st.session_state.bots[i]['actif'] else 'OFF'}")
        st.experimental_rerun()

st.divider()
for m in reversed(st.session_state.logs[-12:]):
    st.write(m)
