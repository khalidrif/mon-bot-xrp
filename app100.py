# --- 7. LOGIQUE LIVE & SYNCHRO RÉELLE (SCANNER TOTAL) ---
px, cash_total = 0.0, 0.0
if kraken:
    try:
        if not kraken.markets: kraken.load_markets()
        ticker = kraken.fetch_ticker('XRP/USDC')
        px, bal = ticker['last'], kraken.fetch_balance()
        cash_total = bal.get('USDC', {}).get('total', 0.0)
        
        # --- RÉCUPÉRATION DES ORDRES OUVERTS SUR KRAKEN ---
        open_orders = kraken.fetch_open_orders('XRP/USDC')
        oids_ouverts = [o['id'] for o in open_orders]

        for name, bot in st.session_state.bots.items():
            if bot["status"] != "LIBRE" and bot["oid"] != "NONE":
                
                # SI L'ORDRE N'EST PLUS DANS LA LISTE DES ORDRES OUVERTS KRAKEN
                if bot["oid"] not in oids_ouverts:
                    try:
                        # On vérifie si c'est bien exécuté (closed)
                        check = kraken.fetch_order(bot["oid"])
                        if check['status'] == 'closed':
                            old_status = bot["status"]
                            st.session_state.bots[name]["oid"] = "NONE" 
                            
                            if old_status == "ACHAT":
                                # 1. PASSAGE EN VENTE (L'ACHAT EST FINI)
                                vol_v = float(kraken.amount_to_precision('XRP/USDC', (bot["budget"] + bot.get("gain", 0)) / bot["pa"]))
                                v_res = kraken.create_limit_sell_order('XRP/USDC', vol_v, bot["pv"])
                                st.session_state.bots[name].update({"status": "VENTE", "oid": v_res['id']})
                            
                            elif old_status == "VENTE":
                                # 2. VENTE FINIE -> RELANCE AUTO ACHAT
                                profit = (float(bot["pv"]) - float(bot["pa"])) * (bot["budget"] / bot["pa"])
                                st.session_state.profit_total += profit
                                st.session_state.daily_gain += profit
                                
                                pa_f = float(kraken.price_to_precision('XRP/USDC', bot["pa"]))
                                vol_a = float(kraken.amount_to_precision('XRP/USDC', (bot["budget"] + bot.get("gain", 0) + profit) / pa_f))
                                a_res = kraken.create_limit_buy_order('XRP/USDC', vol_a, pa_f, {'post-only': True})
                                
                                st.session_state.bots[name].update({
                                    "status": "ACHAT", "oid": a_res['id'], 
                                    "cycles": int(bot.get("cycles", 0)) + 1, 
                                    "gain": float(bot.get("gain", 0)) + profit
                                })
                            
                            sauvegarder(st.session_state.bots, st.session_state.profit_total, st.session_state.daily_gain, datetime.now().strftime("%Y-%m-%d"))
                            st.rerun() # Refresh immédiat pour voir le changement
                    except:
                        # Si l'ordre a été annulé manuellement
                        st.session_state.bots[name].update({"status": "LIBRE", "oid": "NONE"})
    except:
        st.caption("🔄 Synchro Kraken...")
