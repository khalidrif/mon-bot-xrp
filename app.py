# Sélection du bot
id_bot = st.selectbox(
    "Bot n°",
    range(1, 51),
    key=f"bot_select_sidebar_{st.session_state.session_uid}"
)
bot = st.session_state.bots[id_bot]

# Activation du bot
bot["actif"] = st.toggle(
    "Activer",
    bot["actif"],
    key=f"actif_{id_bot}_{st.session_state.session_uid}"
)

# Paramètres du bot
bot["p_achat"] = st.number_input(
    "Prix Achat",
    value=bot["p_achat"],
    format="%.4f",
    key=f"p_achat_{id_bot}_{st.session_state.session_uid}"
)
bot["p_vente"] = st.number_input(
    "Prix Vente",
    value=bot["p_vente"],
    format="%.4f",
    key=f"p_vente_{id_bot}_{st.session_state.session_uid}"
)
bot["mise"] = st.number_input(
    "Mise (USDC)",
    value=bot["mise"],
    format="%.4f",
    key=f"mise_{id_bot}_{st.session_state.session_uid}"
)

# --- Bouton Sauvegarder ---
if st.button("💾 Sauvegarder", key=f"save_{id_bot}_{st.session_state.session_uid}"):
    save_config(st.session_state.bots)
    st.toast(f"Bot {id_bot} sauvegardé ✔")

# --- Bouton Réinitialiser ---
if st.button("🗑 Réinitialiser le bot", key=f"reset_{id_bot}_{st.session_state.session_uid}"):
    reset_bot(id_bot)

st.divider()

# --- Boutons Démarrer et Stop ---
def start_bots():
    st.session_state.run = True
    st.session_state.stop_clicked = False
    if st.session_state.start_time is None:
        st.session_state.start_time = datetime.datetime.now()
        st.session_state.trade_count = 0
        st.session_state.start_capital = sum(b["mise"] for b in st.session_state.bots.values())

def stop_bots():
    st.session_state.run = False
    st.session_state.stop_clicked = True

st.button("🚀 Démarrer", on_click=start_bots, key=f"start_{st.session_state.session_uid}")
st.button("🛑 Stop", on_click=stop_bots, key=f"stop_{st.session_state.session_uid}")
