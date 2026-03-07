st.subheader("Diagnostic Kraken")

test_buy = api.query_private("AddOrder", {
    "pair": "XRPRLUSD",
    "type": "buy",
    "ordertype": "market",
    "volume": 5   # 5 XRP = minimum Kraken
})

st.error(test_buy)
