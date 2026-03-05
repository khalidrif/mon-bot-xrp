# --- MAIN LOOP (AFFICHAGE DES 100 LIGNES GARANTI) ---
live = st.empty()
count = 0
while True:
    try:
        px = kraken.fetch_ticker('XRP/USDC')['last']
        if count % 5 == 0: 
            bal = kraken.fetch_balance()
            st.session_state.bankroll = bal.get('USDC', {}).get('free', 0.0)
        
        with live.container():
            st.write(f"### MARKET FEED : {px:.4f} XRP/USDC")
            c1, c2, c3 = st.columns(3)
            c1.metric("BANKROLL", f"{st.session_state.bankroll:.2f} USDC")
            c2.metric("NET GAIN", f"+{st.session_state.profit_total:.4f}")
            c3.metric("BOTS ON", len([n for n, b in st.session_state.bots.items() if b["status"] != "LIBRE"]))
            st.divider()
            
            # ICI : ON FORCE L'AFFICHAGE DES 100 BOTS
            for i in range(100):
                name = f"B{i+1}"
                bot = st.session_state.bots[name]
                
                # Logique de mise à jour si actif
                if bot["status"] != "LIBRE" and count % 2 == 0:
                    try:
                        info = kraken.fetch_order(bot["oid"])
                        if info['status'] == 'closed':
                            if bot["status"] == "ACHAT":
                                st.session_state.bots[name]["status"] = "VENTE"
                                vol = float(kraken.amount_to_precision('XRP/USDC', (bot["budget"]+bot["gain"]) / bot["pa"]))
                                v_res = kraken.create_limit_sell_order('XRP/USDC', vol, bot["pv"])
                                st.session_state.bots[name]["oid"] = v_res['id']
                            else: # Cycle vente terminé
                                g = (bot["pv"] - bot["pa"]) * (bot["budget"] / bot["pa"])
                                st.session_state.profit_total += g
                                st.session_state.bots[name].update({"status": "LIBRE", "gain": bot["gain"]+g, "cycles": bot["cycles"]+1})
                            sauvegarder(st.session_state.bots, st.session_state.profit_total)
                    except: pass

                # AFFICHAGE DE LA LIGNE (Même si LIBRE)
                st_label = bot["status"]
                if st_label == "LIBRE":
                    # Ligne grise pour les bots inactifs
                    st.markdown(f'<div class="bot-line"><span class="bot-id">{name}</span><span style="color:#333;">IDLE</span><span style="color:#222;">---</span><span style="color:#222;">0.00 $</span></div>', unsafe_allow_html=True)
                else:
                    # Ligne Bloomberg pour les bots actifs
                    sc = "#00FF00" if st_label == "VENTE" else "#FFA500"
                    val = bot["budget"] + bot["gain"]
                    st.markdown(f'''
                        <div class="bot-line">
                            <span class="bot-id">{name}</span>
                            <span style="color:{sc}; font-weight:bold;">{st_label}</span>
                            <span>{bot["pa"]} → {bot["pv"]}</span>
                            <span class="flash-box">{bot.get("cycles", 0)} CYC</span>
                            <span class="flash-box">{val:.2f} $</span>
                        </div>''', unsafe_allow_html=True)
    except: pass
    count += 1
    time.sleep(10)
