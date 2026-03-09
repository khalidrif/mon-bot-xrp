import streamlit as st
import ccxt
import json, os, time

st.set_page_config(page_title="Snowball XRP", page_icon="❄️", layout="wide")

SAVE_FILE="bots.json"

# -----------------------
# LOAD SAVE
# -----------------------

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
    st.session_state.bots=load_bots()

# -----------------------
# MIGRATION
# -----------------------

for bot in st.session_state.bots:

    bot.setdefault("enabled",False)
    bot.setdefault("mode","CONFIG")
    bot.setdefault("target_usdc",10.0)
    bot.setdefault("buy_price",0.0)
    bot.setdefault("sell_price",0.0)
    bot.setdefault("xrp_qty",0.0)
    bot.setdefault("snowball",True)
    bot.setdefault("gain",0.0)
    bot.setdefault("cycles",0)
    bot.setdefault("pair","XRP/USDC")
    bot.setdefault("buy_id","")
    bot.setdefault("sell_id","")

save_bots()

# -----------------------
# CONNECT KRAKEN
# -----------------------

exchange=ccxt.kraken({
"apiKey":st.secrets["KRAKEN_KEY"],
"secret":st.secrets["KRAKEN_SECRET"],
"enableRateLimit":True
})

# -----------------------
# PRICE
# -----------------------

def get_price():
    for p in ["XRP/USDC","XRP/USDT","XRP/USD"]:
        try:
            return exchange.fetch_ticker(p)["last"]
        except:
            pass
    return None

prix=get_price()

st.title("❄️ Snowball XRP Bot")

if prix:
    st.metric("Prix XRP",f"{prix:.5f}")

# -----------------------
# BALANCE
# -----------------------

bal=exchange.fetch_balance()

usd=bal["free"].get("USDC",0)+bal["free"].get("USDT",0)+bal["free"].get("USD",0)
xrp=bal["free"].get("XRP",0)

st.metric("USD Disponible",f"{usd:.2f}")
st.metric("XRP Disponible",f"{xrp:.2f}")

# -----------------------
# ADD BOT
# -----------------------

if st.button("➕ Ajouter Bot"):

    st.session_state.bots.append({
        "enabled":False,
        "mode":"CONFIG",
        "target_usdc":10,
        "buy_price":0,
        "sell_price":0,
        "xrp_qty":0,
        "snowball":True,
        "gain":0,
        "cycles":0,
        "pair":"XRP/USDC",
        "buy_id":"",
        "sell_id":""
    })

    save_bots()
    st.rerun()

# -----------------------
# DISPLAY BOTS
# -----------------------

st.subheader("Bots actifs")

for i,bot in enumerate(st.session_state.bots):

    col1,col2,col3,col4,col5,col6,col7=st.columns(7)

    bot["target_usdc"]=col1.number_input("USDC",value=float(bot["target_usdc"]),key=f"u{i}")
    bot["buy_price"]=col2.number_input("BUY",value=float(bot["buy_price"]),format="%.5f",key=f"b{i}")
    bot["sell_price"]=col3.number_input("SELL",value=float(bot["sell_price"]),format="%.5f",key=f"s{i}")

    bot["snowball"]=col4.checkbox("Snowball",value=bot["snowball"],key=f"sn{i}")

    col5.write(f"Gain {bot['gain']:.4f}")
    col6.write(f"Cycles {bot['cycles']}")

    if not bot["enabled"]:

        if col7.button("Start",key=f"start{i}"):

            try:

                qty=round(bot["target_usdc"]/bot["buy_price"],4)

                order=exchange.create_limit_buy_order(
                    bot["pair"],
                    qty,
                    bot["buy_price"]
                )

                bot["buy_id"]=order["id"]
                bot["xrp_qty"]=qty
                bot["mode"]="BUY"
                bot["enabled"]=True

                time.sleep(1)

            except Exception as e:
                st.error(e)

            save_bots()
            st.rerun()

    else:

        if col7.button("Stop",key=f"stop{i}"):

            bot["enabled"]=False
            bot["mode"]="CONFIG"

            save_bots()
            st.rerun()

# -----------------------
# TRADING LOOP
# -----------------------

for bot in st.session_state.bots:

    if not bot["enabled"]:
        continue

    # WAIT BUY
    if bot["mode"]=="BUY":

        try:
            order=exchange.fetch_order(bot["buy_id"],bot["pair"])
        except:
            continue

        if order["status"]=="closed":

            try:

                sell=exchange.create_limit_sell_order(
                    bot["pair"],
                    bot["xrp_qty"],
                    bot["sell_price"]
                )

                bot["sell_id"]=sell["id"]
                bot["mode"]="SELL"

                time.sleep(1)

            except:
                pass

            save_bots()

        continue

    # WAIT SELL
    if bot["mode"]=="SELL":

        try:
            order=exchange.fetch_order(bot["sell_id"],bot["pair"])
        except:
            continue

        if order["status"]=="closed":

            gain=(bot["sell_price"]-bot["buy_price"])*bot["xrp_qty"]

            bot["gain"]+=gain
            bot["cycles"]+=1

            if bot["snowball"]:
                bot["target_usdc"]+=gain

            # NEW BUY (snowball loop)

            try:

                qty=round(bot["target_usdc"]/bot["buy_price"],4)

                buy=exchange.create_limit_buy_order(
                    bot["pair"],
                    qty,
                    bot["buy_price"]
                )

                bot["buy_id"]=buy["id"]
                bot["xrp_qty"]=qty
                bot["mode"]="BUY"

                time.sleep(1)

            except:
                bot["mode"]="CONFIG"

            save_bots()

# -----------------------
# AUTO LOOP
# -----------------------

time.sleep(2)
st.rerun()
