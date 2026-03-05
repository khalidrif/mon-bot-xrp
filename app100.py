# --- BOUCLE AVEC DEBUG KRAKEN ---
count = 0
while True:
    try:
        if not kraken.markets: kraken.load_markets()
        
        ticker = kraken.fetch_ticker('XRP/USDC')
        px = ticker['last']
        
        if count % 10 == 0:
            bal = kraken.fetch_balance()
            st.session_state.bankroll = bal.get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET FEED - XRP/USDC (LIVE)")
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{st.session_state.bankroll:.2f} USDC")
            c2.metric("XRP PRICE", f"{px:.4f}")
            c3.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            st.divider()
            
            actifs = [n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]
            selection = actifs[(count % max(1, len(actifs)//5 + 1))*5 : (count % max(1, len(actifs)//5 + 1))*5 + 5]
            
            for name in actifs:
                bot = st.session_state.bots[name]
                val_snow = budget_base + bot['gain']
                vol = float(kraken.amount_to_precision('XRP/USDC', val_snow / px))
                
                if name in selection:
                    # --- LOGIQUE ACHAT AVEC CAPTURE D'ERREUR ---
                    if bot["status"] == "ACHAT" and px <= bot["p_achat"]:
                        try:
                            res = kraken.create_limit_buy_order('XRP/USDC', vol, bot["p_achat"])
                            st.session_state.bots[name]["status"] = "VENTE"
                            st.toast(f"✅ ORDRE KRAKEN ACTIVE : {res['id']}")
                        except Exception as e:
                            # AFFICHE L'ERREUR REELLE DE KRAKEN ICI
                            st.error(f"🔴 REFUS KRAKEN {name}: {str(e)}")

                    # --- LOGIQUE VENTE AVEC CAPTURE D'ERREUR ---
                    elif bot["status"] == "VENTE" and px >= bot["p_vente"]:
                        try:
                            res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["p_vente"])
                            g = (bot['p_vente'] - bot['p_achat']) * vol
                            st.session_state.profit_total += g
                            st.session_state.bots[name].update({"gain": bot["gain"]+g, "cycles": bot["cycles"]+1, "status": "ACHAT"})
                            st.toast(f"💰 VENTE KRAKEN ACTIVE : {res['id']}")
                        except Exception as e:
                            st.error(f"🔴 REFUS KRAKEN {name}: {str(e)}")
                    
                    time.sleep(1.0)

                sc = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                st.markdown(f'<div class="bot-line"><span>{name}</span><span style="color:{sc};">{bot["status"]}</span><span>{bot["p_achat"]}->{bot["p_vente"]}</span><span class="flash-box">{val_snow:.2f} USDC</span></div>', unsafe_allow_html=True)
            
        count += 1
        sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)

    except Exception as e:
        if "Rate limit" in str(e):
            st.warning("⚠️ Surcharge API. Pause 60s...")
            time.sleep(60)
        else: st.write(f"SYSTEM: {str(e)[:50]}")
    
    time.sleep(30)
