    # --- DANS CHAQUE COLONNE (Exemple pour Bot 1) ---
    with c1:
        st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
        st.subheader("🚜 BOT 1")
        p1_in = st.number_input("ACHAT 1", value=1.3600, format="%.4f", key="p1i")
        p1_out = st.number_input("VENTE 1", value=1.3800, format="%.4f", key="p1o")
        
        col_b1, col_a1 = st.columns(2)
        if col_b1.button("🚀 LANCER", key="run1"):
            vol = (usdc_reel * 0.95 / 2) / prix_actuel
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p1_out}}
            kraken.create_limit_buy_order('XRP/USDC', vol, p1_in, params)
            st.success("B1 Lancé")

        # BOUTON POUR ANNULER UNIQUEMENT CE BOT
        if col_a1.button("🗑️ STOP", key="stop1"):
            orders = kraken.fetch_open_orders('XRP/USDC')
            for o in orders:
                if float(o['price']) == p1_in:
                    kraken.cancel_order(o['id'])
                    st.warning(f"Bot 1 ({p1_in}) annulé")
                    time.sleep(1)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # REPRODUIRE LA MÊME LOGIQUE POUR c2 ET c3 (en changeant les prix p2_in, p3_in)
