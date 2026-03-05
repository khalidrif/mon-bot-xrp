    if st.button(f"🚀 ACTIVER {bot_sel}", use_container_width=True):
        if kraken:
            try:
                if not kraken.markets: kraken.load_markets()
                pa_f = float(kraken.price_to_precision('XRP/USDC', p_in))
                vol = float(kraken.amount_to_precision('XRP/USDC', b_val / pa_f))
                
                # ENVOI KRAKEN
                res = kraken.create_limit_buy_order('XRP/USDC', vol, pa_f, {'post-only': True})
                
                # MISE À JOUR MÉMOIRE
                st.session_state.bots[bot_sel].update({
                    "status": "ACHAT", 
                    "pa": pa_f, 
                    "pv": p_out, 
                    "oid": res['id'], 
                    "budget": b_val
                })
                
                # SAUVEGARDE ET RECHARGEMENT IMMÉDIAT
                sauvegarder(st.session_state.bots, st.session_state.profit_total, st.session_state.historique)
                st.rerun() # <--- C'EST CETTE LIGNE QUI FAIT APPARAÎTRE LE BOT TOUT DE SUITE
                
            except Exception as e: 
                st.error(f"Kraken: {e}")
