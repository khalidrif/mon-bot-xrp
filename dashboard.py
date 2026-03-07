    # --- BOUTONS DE LANCEMENT ET ANNULATION ---
    st.write("")
    l1, l2 = st.columns(2)

    # Volume : on prend environ 48% du solde disponible pour chaque bot
    vol_test = (usdc_reel * 0.48) / prix_actuel if usdc_reel > 14 else 0

    with l1:
        if st.button("🚀 LANCER BOT 1"):
            if usdc_reel > 14:
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p1_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol_test, p1_in, params)
                st.success("✅ Bot 1 actif")
            else: st.error("Solde < 14$")
        
        # NOUVEAU : Bouton pour annuler uniquement le Bot 1
        if st.button("🗑️ ANNULER BOT 1", key="cancel1"):
            # Note: Cette fonction cherche l'ordre à 1.36 pour l'annuler
            st.warning("Annulation manuelle requise sur Kraken ou via Reset.")

    with l2:
        if st.button("🚀 LANCER BOT 2"):
            if usdc_reel > 14:
                params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': p2_out}}
                kraken.create_limit_buy_order('XRP/USDC', vol_test, p2_in, params)
                st.success("✅ Bot 2 actif")
            else: st.error("Solde < 14$")
            
        # NOUVEAU : Bouton pour annuler uniquement le Bot 2
        if st.button("🗑️ ANNULER BOT 2", key="cancel2"):
            st.warning("Annulation manuelle requise sur Kraken ou via Reset.")

    st.divider()
    if st.button("🚨 ANNULER TOUT (RESET COMPLET)", use_container_width=True):
        kraken.cancel_all_orders('XRP/USDC')
        st.rerun()
