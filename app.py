# ----------------------------------------------------
# DISPLAY BOTS — VERSION CORRIGÉE
# ----------------------------------------------------
for i, bot in enumerate(st.session_state.bots):

    st.markdown("---")

    colStatus, colUSDC, colBuy, colSell, colSnow, colGain, colCycles, colMarket, colStart, colDelete = st.columns([1,3,3,3,2,2,2,2,2,1])

    # ICON
    if bot["mode"] == "CONFIG":
        colStatus.write("⚙️")
    elif bot["mode"] == "BUY":
        colStatus.write("🟢")
    elif bot["mode"] == "SELL":
        colStatus.write("🔴")
    else:
        colStatus.write("🟡")

    # INPUTS
    bot["target_usdc"] = colUSDC.number_input("", value=float(bot["target_usdc"]), key=f"u{i}", label_visibility="collapsed")
    colUSDC.caption("Montant")

    bot["buy_price"] = colBuy.number_input("", value=float(bot["buy_price"]), format="%.5f", key=f"b{i}", label_visibility="collapsed")
    colBuy.caption("Achat")

    bot["sell_price"] = colSell.number_input("", value=float(bot["sell_price"]), format="%.5f", key=f"s{i}", label_visibility="collapsed")
    colSell.caption("Vente")

    bot["snowball"] = colSnow.checkbox("Snowball", value=bot["snowball"], key=f"sn{i}")

    # GAIN (petit)
    colGain.markdown(f"<div style='font-size:14px;'><b>Gain</b><br>{bot['gain']:.4f}</div>", unsafe_allow_html=True)

    # CYCLES (petit)
    colCycles.markdown(f"<div style='font-size:14px;'><b>Cycles</b><br>{bot['cycles']}</div>", unsafe_allow_html=True)

    # REMPLACE MARCHE PAR QUANTITÉ XRP
    colMarket.markdown(
        f"<div style='text-align:center;font-size:14px;'><b>Quantité</b><br>{bot['xrp_qty']}</div>",
        unsafe_allow_html=True
    )

    # START / STOP
    if not bot["enabled"]:
        if colStart.button("Start", key=f"start{i}"):
            bot["enabled"] = True
            try:
                qty = round(bot["target_usdc"] / bot["buy_price"], 6)
                exchange.create_limit_buy_order("XRP/USDC", qty, bot["buy_price"])
                bot["xrp_qty"] = qty
                bot["mode"] = "BUY"
            except:
                bot["enabled"] = False
                bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()
    else:
        if colStart.button("Stop", key=f"stop{i}"):
            bot["enabled"] = False
            bot["mode"] = "CONFIG"
            save_bots()
            st.rerun()

    # DELETE
    if colDelete.button("🗑️", key=f"del{i}"):
        del st.session_state.bots[i]
        save_bots()
        st.rerun()
