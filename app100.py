# --- RÉCUPÉRATION DONNÉES LIVE & SURVEILLANCE ---
px, cash = 0.0, 0.0
if kraken:
    try:
        # 1. On force le rechargement propre
        kraken.load_markets(True) 
        
        # 2. Ticker avec petit délai pour éviter le spam
        time.sleep(0.5)
        ticker = kraken.fetch_ticker('XRP/USDC')
        px = ticker['last']
        
        # 3. Balance
        bal = kraken.fetch_balance()
        cash = bal.get('USDC', {}).get('free', 0.0)

        # 4. SURVEILLANCE DES ORDRES ACTIFS
        for name, bot in st.session_state.bots.items():
            if bot["status"] != "LIBRE" and bot["oid"] != "NONE":
                try:
                    order = kraken.fetch_order(bot["oid"])
                    # SI ACHAT FINI -> PLACER VENTE
                    if order['status'] == 'closed' and bot["status"] == "ACHAT":
                        vol_v = float(kraken.amount_to_precision('XRP/USDC', (bot["budget"]+bot.get("gain",0))/bot["pa"]))
                        pv_f = float(kraken.price_to_precision('XRP/USDC', bot["pv"]))
                        v_res = kraken.create_limit_sell_order('XRP/USDC', vol_v, pv_f)
                        st.session_state.bots[name].update({"status": "VENTE", "oid": v_res['id']})
                        sauvegarder(st.session_state.bots, st.session_state.profit_total)
                    
                    # SI VENTE FINIE -> PROFIT + CYCLE
                    elif order['status'] == 'closed' and bot["status"] == "VENTE":
                        profit = (bot["pv"] - bot["pa"]) * (bot["budget"]/bot["pa"])
                        st.session_state.profit_total += profit
                        st.session_state.bots[name].update({"status": "LIBRE", "oid": "NONE", "cycles": bot.get("cycles", 0)+1, "gain": bot.get("gain", 0)+profit})
                        sauvegarder(st.session_state.bots, st.session_state.profit_total)
                except: continue # Si un ordre bug, on passe au suivant
    except Exception as e:
        # Si ça bug, on affiche l'erreur discrètement en bas
        st.caption(f"Note: Synchro Kraken en cours... ({str(e)[:40]})")
