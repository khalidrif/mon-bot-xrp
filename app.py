for i, bot in enumerate(st.session_state.bots):

    st.markdown("----")

    # 1 ligne horizontale
    col0, col1, col2, col3, col4, col5, col6 = st.columns([1,3,3,3,2,2,1])

    # ICON STATUS
    if bot["mode"] == "CONFIG":
        col0.write("⚙️")
    elif bot["mode"] == "BUY":
        col0.write("🟢")
    elif bot["mode"] == "SELL":
        col0.write("🔴")
    else:
        col0.write("🟡")

    # INPUTS SUR UNE SEULE LIGNE
    bot["target_usdc"] = col1.number_input(
        "Montant",
        value=float(bot["target_usdc"]),
        key=f"u{i}"
    )

    bot["buy_price"] = col2.number_input(
        "Achat",
        value=float(bot["buy_price"]),
        min_value=0.0,
        format="%.5f",
        key=f"b{i}"
    )

    bot["sell_price"] = col3.number_input(
        "Vente",
        value=float(bot["sell_price"]),
        min_value=0.0,
        format="%.5f",
        key=f"s{i}"
    )

    bot["snowball"] = col4.checkbox(
        "Snowball",
        value=bot["snowball"],
        key=f"sn{i}"
    )

    # START / STOP
    if not bot["enabled"]:
        if col5.button("Start", key=f"start{i}"):
            bot["enabled"] = True
            try:
                qty = round(bot["target_usdc"] / bot["buy_price"], 6)
                order = exchange.create_limit_buy_order(
                    "XRP/USDC", qty, bot["buy_price"]
                )
                bot["xrp_qty"] = qty
                bot["mode"] = "BUY"
            except:
                bot["enabled"] = False
                bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()
    else:
        if col5.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()

    # DELETE
    if col6.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()

    # GAINS ET CYCLES SUR UNE 2ᵉ LIGNE
    colG1, colG2 = st.columns(2)
    colG1.metric("Gain", f"{bot['gain']:.4f}")
    colG2.metric("Cycles", bot["cycles"])
