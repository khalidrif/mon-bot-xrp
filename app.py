import streamlit as st
import time
import krakenex
import threading
import pandas as pd

running = False
profit_net = 0.0

# -------------------------------------------------------
# CONFIG API KRAKEN (Secrets Streamlit)
# -------------------------------------------------------
api = krakenex.API()
api.key = st.secrets["KRAKEN_API_KEY"]
api.secret = st.secrets["KRAKEN_API_SECRET"]

PAIR = "XXRPZUSD"   # XRP / USDC sur Kraken (USD = USDC/stablecoins)

# -------------------------------------------------------
# Kraken helpers
# -------------------------------------------------------
def get_price():
    data = api.query_public("Ticker", {"pair": PAIR})
    return float(data["result"][PAIR]["c"][0])

def get_usdc_balance():
    balance = api.query_private("Balance")
    if "result" in balance and "USDC" in balance["result"]:
        return float(balance["result"]["USDC
