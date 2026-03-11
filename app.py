# --- 4. BOUCLE DE TRADING (VERSION TRIPLE VERROU) ---
def run_cycle():
    try:
        # On force Kraken à ignorer son cache avec un nonce frais
        ticker = exchange.fetch_ticker(symbol, params={'nonce': str(int(time.time()*1000))})
        price = float((ticker["bid"] + ticker["ask"]) / 2)
        st.session_state.price = price
        
        bal = exchange.fetch_balance()
        usdc_dispo = float(bal['free'].get('USDC', 0.0))
        st.session_state.usdc = usdc_dispo
        st.session_state.xrp = bal['free'].get('XRP', 0.0)
        log(f"🎯 Flux : {price:.5f}")
    except: 
        return

    if not st.session_state.run: return

    for i, bot in st.session_state.bots.items():
        # VERROU 1 : On ignore si le bot est inactif ou déjà en cours (pending)
        if not bot.get("actif") or i in st.session_state.pending_orders: 
            continue
        
        mise_actu = float(bot["mise"] + bot["gain_cumule"])
        p_achat = float(bot["p_achat"])
        p_vente = float(bot["p_vente"])

        # --- LOGIQUE ACHAT ---
        if bot["etape"] == "ATTENTE_ACHAT" and price <= p_achat:
            if usdc_dispo >= mise_actu:
                st.session_state.pending_orders.add(i) # VERROU 2 : On bloque l'ID
                try:
                    qty = float(exchange.amount_to_precision(symbol, (mise_actu * 0.98) / price))
                    
                    # VERROU 3 : On change l'étape AVANT l'ordre pour éviter la répétition
                    bot["etape"] = "EN_COURS_ACHAT" 
                    
                    exchange.create_market_buy_order(symbol, qty)
                    
                    bot.update({"qty": qty, "etape": "ATTENTE_VENTE"})
                    log(f"✅ Bot {i} : ACHAT RÉUSSI")
                    time.sleep(2) # PAUSE DE SÉCURITÉ
                except:
                    bot["etape"] = "ATTENTE_ACHAT" # Reset si erreur
                    log(f"❌ Erreur Achat {i}")
                finally:
                    st.session_state.pending_orders.discard(i)

        # --- LOGIQUE VENTE ---
        elif bot["etape"] == "ATTENTE_VENTE" and price >= p_vente:
            if bot.get("qty", 0) > 0:
                st.session_state.pending_orders.add(i) # VERROU 2
                try:
                    qty_sell = float(exchange.amount_to_precision(symbol, bot["qty"] * 0.995))
                    
                    # VERROU 3 : Change l'étape AVANT
                    bot["etape"] = "EN_COURS_VENTE"
                    
                    exchange.create_market_sell_order(symbol, qty_sell)
                    
                    gain = (price * qty_sell) - mise_actu
                    bot.update({"gain_cumule": bot["gain_cumule"] + gain, "cycles": bot.get("cycles",0)+1, "qty": 0, "etape": "ATTENTE_ACHAT"})
                    log(f"💰 Bot {i} : VENTE RÉUSSIE (+{gain:.2f}$)")
                    time.sleep(2) # PAUSE DE SÉCURITÉ
                except:
                    bot["etape"] = "ATTENTE_VENTE" # Reset si erreur
                    log(f"❌ Erreur Vente {i}")
                finally:
                    st.session_state.pending_orders.discard(i)
