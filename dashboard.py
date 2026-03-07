# --- DANS CHAQUE DOSSIER (Exemple pour Bot 1) ---
with st.expander(f"🚜 BOT {p_idx} - RÉGLAGES", expanded=(i==0)):
    st.markdown("<div class='bot-card'>", unsafe_allow_html=True)
    p_in = st.number_input(f"ACHAT", value=prices_in[i], format="%.4f", key=f"in{i}")
    p_out = st.number_input(f"VENTE", value=round(p_in + 0.02, 4), format="%.4f", key=f"out{i}")
    
    col_l, col_s = st.columns(2)
    
    # BOUTON POUR LANCER
    if col_l.button(f"🚀 LANCER B{p_idx}", key=f"run{i}"):
        if usdc_dispo > 13.5:
            params = {'close': {'ordertype': 'limit', 'type': 'sell', 'price': round(p_out, 4)}}
            kraken.create_limit_buy_order('XRP/USDC', vol_auto, round(p_in, 4), params)
            st.success("Lancé !")
            st.balloons()
        else: st.error("Solde < 14$")
    
    # BOUTON POUR ANNULER UNIQUEMENT CE BOT
    if col_s.button(f"🗑️ STOP B{p_idx}", key=f"stop{i}"):
        orders = kraken.fetch_open_orders('XRP/USDC')
        for o in orders:
            # On compare le prix de l'ordre avec le prix du bot
            if float(o['price']) == p_in:
                kraken.cancel_order(o['id']) # On annule seulement cet ID
                st.warning(f"Bot {p_idx} arrêté")
                time.sleep(1)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
