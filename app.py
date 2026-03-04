            for i in range(10):
                name = f"Bot_{i+1}"
                bot = st.session_state.bots[name]
                with all_cols[i]:
                    st.write(f"### 🤖 {i+1}")
                    
                    # --- CALCUL DE LA VALEUR EN DIRECT ---
                    budget_initial_bot = budget_in + bot['gain']
                    
                    if bot["status"] == "ATTENTE_ACHAT":
                        # La valeur est égale au cash qui attend d'être utilisé
                        valeur_actuelle = budget_initial_bot
                        st.warning(f"📥 ACHAT @{bot['p_achat']}")
                    
                    elif bot["status"] == "ATTENTE_VENTE":
                        # On récupère l'info de l'ordre pour savoir combien on a de XRP
                        info_v = kraken.fetch_order(bot['id'], 'XRP/USDC')
                        quantite_xrp = info_v['amount']
                        # Valeur = XRP possédés x Prix actuel du marché
                        valeur_actuelle = quantite_xrp * prix_reel
                        st.success(f"📤 VENTE @{bot['p_vente']}")
                    
                    else:
                        valeur_actuelle = 0.0
                        st.caption("Libre")

                    # --- AFFICHAGE DES STATS DU BOT ---
                    st.write(f"🔄 Cycles: {bot['cycles']}")
                    st.write(f"💰 Gain Net: {bot['gain']:.4f}$")
                    # On affiche la valeur en JAUNE si elle monte !
                    st.metric("Valeur Live", f"{valeur_actuelle:.2f} $", 
                              delta=f"{valeur_actuelle - budget_in:.4f}$" if valeur_actuelle > 0 else None)
