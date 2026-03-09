import streamlit as st
import ccxt
import json, os, time
import pandas as pd

st.set_page_config(page_title="Snowball XRP", page_icon="❄️", layout="wide")

SAVE_FILE = "bots.json"

def load_bots():
    if not os.path.exists(SAVE_FILE):
        return []
    try:
        with open(SAVE_FILE,"r") as f:
            return json.load(f)
    except:
        return []

def save_bots():
    with open(SAVE_FILE,"w") as f:
        json.dump(st.session_state.bots,f,indent=4)

if "bots" not in st.session_state:
    st.session_state.bots = load_bots()

# migration
for bot in st.session_state.bots:
    bot.setdefault("enabled",False)
    bot.setdefault("mode","CONFIG")
    bot.setdefault("target_usdc",0.0)
    bot.setdefault("buy_price",0.0)
    bot.setdefault("sell_price",0.0)
    bot.setdefault("xrp_qty",0.0)
    bot.setdefault("snowball",True)
    bot.setdefault("gain",0.0)
    bot.setdefault("cycles",0)
    bot.setdefault("last_usdc_value",0.0)
    bot.setdefault("pair","XRP/USDC")

save_bots()

if "last_run" not in st.session_state:
    st.session_state.last_run = 0

# connect kraken
try:
    exchange = ccxt.kraken({
        "apiKey": st.secrets["KRAKEN_KEY"],
        "secret": st.secrets["KRAKEN_SECRET"],
        "enableRateLimit": True
    })
except:
    st.error("Erreur API Kraken")
    st.stop()

def get_price():
    for p in ["XRP/USDC","XRP/USDT","XRP/USD"]:
        try:
            return exchange.fetch_ticker(p)["last"]
        except:
            pass
    return None

prix = get_price()
if prix is None:
    st.error("Impossible prix Kraken")
    st.stop()

st.title("❄️ Bot Snowball XRP")
st.metric("Prix",f"{prix:.5f}")

# balances
bal = exchange.fetch_balance()
usd = bal["free"].get("USDC",0)+bal["free"].get("USDT",0)+bal["free"].get("USD",0)
xrp = bal["free"].get("XRP",0)

st.metric("USDC/USDT/USD",f"{usd:.4f}")
st.metric("XRP",f"{xrp:.4f}")

# reset
if "reset_lock" not in st.session_state:
    st.session_state.reset_lock=False

if st.button("🧹 Reset Bots") and not st.session_state.reset_lock:
    st.session_state.reset_lock=True
    st.session_state.bots=[]
    with open(SAVE_FILE,"w") as f:
        f.write("[]")
    st.success("Reset OK")
    time.sleep(0.3)
    st.session_state.reset_lock=False
    st.rerun()

# add bot
if st.button("➕ Ajouter Bot"):
    st.session_state.bots.append({
        "enabled":False,
        "mode":"CONFIG",
        "target_usdc":0.0,
        "buy_price":0.0,
        "sell_price":0.0,
        "xrp_qty":0.0,
        "snowball":True,
        "gain":0.0,
        "cycles":0,
        "last_usdc_value":0.0,
        "pair":"XRP/USDC"
    })
    save_bots()
    st.rerun()

# display bots
st.subheader("🤖 Vos Bots")

for i,bot in enumerate(st.session_state.bots):

    st.markdown("---")
    colS,colU,colB,colV,colSN,colG,colC,colUSDC,colStart,colDel = st.columns([1,3,3,3,2,2,2,2,2,1])

    if bot["mode"]=="CONFIG": colS.write("⚙️")
    elif bot["mode"]=="BUY": colS.write("🟢")
    elif bot["mode"]=="SELL": colS.write("🔴")
    else: colS.write("🟡")

    bot["target_usdc"]=colU.number_input("",value=float(bot["target_usdc"]),key=f"u{i}",label_visibility="collapsed")
    colU.caption("Montant")

    bot["buy_price"]=colB.number_input("",value=float(bot["buy_price"]),format="%.5f",key=f"b{i}",label_visibility="collapsed")
    colB.caption("Achat")

    bot["sell_price"]=colV.number_input("",value=float(bot["sell_price"]),format="%.5f",key=f"s{i}",label_visibility="collapsed")
    colV.caption("Vente")

    bot["snowball"]=colSN.checkbox("Snowball",value=bot["snowball"],key=f"sn{i}")

    colG.markdown(f"<div style='font-size:14px;'><b>Gain</b><br>{bot['gain']:.4f}</div>",unsafe_allow_html=True)
    colC.markdown(f"<div style='font-size:14px;'><b>Cycles</b><br>{bot['cycles']}</div>",unsafe_allow_html=True)

    usdc_value = bot["xrp_qty"] * prix
    if usdc_value>bot["last_usdc_value"]:
        color="green"
    elif usdc_value<bot["last_usdc_value"]:
        color="red"
    else:
        color="white"

    colUSDC.markdown(f"<div style='font-size:14px;color:{color};'><b>USDC</b><br>{usdc_value:.4f}</div>",unsafe_allow_html=True)

    bot["last_usdc_value"]=usdc_value

    if not bot["enabled"]:
        if colStart.button("Start",key=f"st{i}"):
            bot["enabled"]=True
            try:
                qty=round(bot["target_usdc"]/bot["buy_price"],6)
                order=exchange.create_limit_buy_order("XRP/USDC",qty,bot["buy_price"])
                bot["pair"]=order["symbol"]
                bot["xrp_qty"]=qty
                bot["mode"]="BUY"
            except:
                bot["enabled"]=False
                bot["mode"]="CONFIG"
            save_bots()
            st.rerun()
    else:
        if colStart.button("Stop",key=f"sp{i}"):
            bot["enabled"]=False
            bot["mode"]="CONFIG"
            save_bots()
            st.rerun()

    if colDel.button("🗑️",key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()

# trading loop
now=time.time()
if now-st.session_state.last_run>2:
    st.session_state.last_run=now
    prix=get_price()

    for bot in st.session_state.bots:

        if not bot["enabled"]:
            continue

        if bot["mode"]=="BUY":
            try:
                op=exchange.fetch_open_orders(bot["pair"])
            except:
                op=[]
            if len(op)==0:
                bot["mode"]="SELL"
                save_bots()
            continue

        if bot["mode"]=="SELL":
            if prix<bot["sell_price"]:
                continue
            qty=round(bot["xrp_qty"],6)
            try:
                exchange.create_limit_sell_order(bot["pair"],qty,bot["sell_price"])
            except:
                continue

            bot["gain"]+=(bot["sell_price"]-bot["buy_price"])*qty
            bot["cycles"]+=1

            if bot["snowball"]:
                qty2=round(bot["target_usdc"]/bot["buy_price"],6)
                order2=exchange.create_limit_buy_order(bot["pair"],qty2,bot["buy_price"])
                bot["xrp_qty"]=qty2
                bot["mode"]="BUY"
            else:
                bot["enabled"]=False
                bot["mode"]="CONFIG"

            save_bots()

# unified order fetch
open_orders=[]
closed_orders=[]
for p in ["XRP/USDC","XRP/USDT","XRP/USD"]:
    try: open_orders+=exchange.fetch_open_orders(p)
    except: pass
    try: closed_orders+=exchange.fetch_closed_orders(p)
    except: pass

st.header("📑 Ordres Kraken")

# simple view open
st.subheader("📌 Ordres ouverts")
if not open_orders:
    st.info("Aucun ordre en attente.")
else:
    for o in open_orders:
        c="green" if o["side"]=="buy" else "red"
        d=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(o["timestamp"]/1000))
        st.markdown(f"<div style='font-size:15px;color:{c};'><b>{o['id']}</b> — {o['side']} — {o['price']} — {o['amount']} XRP — {d}</div>",unsafe_allow_html=True)

# simple view closed
st.subheader("📌 Ordres exécutés")
if not closed_orders:
    st.info("Aucun ordre exécuté.")
else:
    for o in closed_orders[-20:]:
        c="green" if o["side"]=="buy" else "red"
        d=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(o["timestamp"]/1000))
        st.markdown(f"<div style='font-size:15px;color:{c};'><b>{o['id']}</b> — {o['side']} — {o['price']} — {o['amount']} XRP — {d}</div>",unsafe_allow_html=True)

# tables
st.subheader("🟡 Tableau ordres ouverts")
if open_orders:
    st.dataframe(pd.DataFrame(open_orders),use_container_width=True)
else:
    st.info("Aucun ordre.")

st.subheader("🟢 Tableau ordres exécutés")
if closed_orders:
    st.dataframe(pd.DataFrame(closed_orders[-20:]),use_container_width=True)
else:
    st.info("Aucun ordre.")

save_bots()
