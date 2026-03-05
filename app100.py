# --- MAIN LOOP SÉCURISÉE ---
live = st.empty()
while True:
    try:
        if not kraken.markets: kraken.load_markets()
        
        ticker = kraken.fetch_ticker('XRP/USDC')
        px = ticker['last']
        bal = kraken.fetch_balance()
        bankroll = bal.get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET FEED - XRP/USDC (LIVE)")
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{bankroll:.2f} USDC")
            c2.metric("XRP PRICE", f"{px:.4f}")
            c3.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            st.divider()
            
            for i in range(100):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                
                if bot["status"] != "LIBRE":
                    val_snow = budget_base + bot['gain']
                    vol = float(kraken.amount_to_precision('XRP/USDC', val_snow / px))
                    
                    # --- ACTION ACHAT ---
                    if bot["status"] == "ACHAT" and px <= bot["p_achat"]:
                        try:
                            # 1. On passe l'ordre REEL
                            ordre = kraken.create_limit_buy_order('XRP/USDC', vol, bot["p_achat"])
                            # 2. MISE À JOUR IMMÉDIATE DE LA MÉMOIRE
                            st.session_state.bots[name]["status"] = "VENTE"
                            # 3. SAUVEGARDE FORCÉE DANS LE FICHIER JSON AVANT TOUT REFRESH
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.toast(f"✅ ACHAT RÉEL Bot {i+1} OK")
                        except Exception as e: 
                            st.error(f"Erreur Achat #{i+1}: {e}")

                    # --- ACTION VENTE ---
                    elif bot["status"] == "VENTE" and px >= bot["p_vente"]:
                        try:
                            # 1. On passe l'ordre REEL
                            ordre = kraken.create_limit_sell_order('XRP/USDC', vol, bot["p_vente"])
                            # 2. CALCUL DU GAIN
                            g = (bot['p_vente'] - bot['p_achat']) * vol
                            st.session_state.profit_total += g
                            # 3. MISE À JOUR DE LA MÉMOIRE
                            st.session_state.bots[name].update({
                                "gain": bot["gain"] + g, 
                                "cycles": bot["cycles"] + 1, 
                                "status": "ACHAT"
                            })
                            # 4. SAUVEGARDE FORCÉE DANS LE FICHIER JSON
                            sauvegarder_donnees(st.session_state.bots, st.session_state.profit_total)
                            st.toast(f"💰 VENTE RÉELLE Bot {i+1} +{g:.2f}")
                        except Exception as e: 
                            st.error(f"Erreur Vente #{i+1}: {e}")
                    
                    # --- AFFICHAGE BLOOMBERG ---
                    sc = "#FFA500" if bot["status"] == "ACHAT" else "#00FF00"
                    st.markdown(f'''
                    <div class="bot-line">
                        <span class="bot-id">#{i+1:02d}</span>
                        <span style="color:{sc}; font-weight:bold;">{bot["status"]}</span>
                        <span>{bot["p_achat"]} → {bot["p_vente"]}</span>
                        <span class="flash-box">{val_snow:.2f} USDC</span>
                        <span class="flash-box">{bot["cycles"]} CYC</span>
                    </div>
                    ''', unsafe_allow_html=True)
                    time.sleep(0.1) # Équilibre Anti-Nonce

    except Exception as e:
        if "nonce" in str(e).lower(): time.sleep(1)
        else: st.write(f"SYSTEM: {str(e)[:50]}")
    
    time.sleep(5)
