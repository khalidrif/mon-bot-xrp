import streamlit as st

st.set_page_config(page_title="XRP Snowball", layout="centered")

# --- État de la Boule de Neige ---
if "capital" not in st.session_state:
    st.session_state.capital = 100.0  # Capital de départ par défaut
if "historique" not in st.session_state:
    st.session_state.historique = []

st.title("❄️ XRP Snowball Bot")

# --- Panneau de contrôle ---
with st.sidebar:
    st.header("Paramètres")
    st.session_state.capital = st.number_input("Capital Actuel (USDC)", value=st.session_state.capital)
    prix_xrp = st.number_input("Prix XRP Actuel", value=1.3400, format="%.4f")

# --- Interface de Trade ---
col1, col2 = st.columns(2)
buy_price = col1.number_input("Prix d'achat cible", value=prix_xrp - 0.01, format="%.4f")
sell_price = col2.number_input("Prix de vente cible", value=prix_xrp + 0.02, format="%.4f")

if st.button("Lancer le cycle et réinvestir 🚀", use_container_width=True):
    # Calcul de la boule de neige
    quantite = st.session_state.capital / buy_price
    nouveau_capital = quantite * sell_price
    profit = nouveau_capital - st.session_state.capital
    
    # Mise à jour du capital (L'effet boule de neige)
    old_cap = st.session_state.capital
    st.session_state.capital = nouveau_capital
    
    # Enregistrement
    st.session_state.historique.append({
        "Achat": buy_price,
        "Vente": sell_price,
        "Ancien Capital": old_cap,
        "Nouveau Capital": nouveau_capital,
        "Profit": profit
    })
    st.balloons()

# --- Affichage des résultats ---
st.metric("Capital Total (Boule de Neige)", f"{round(st.session_state.capital, 2)} USDC", 
          delta=f"{round(st.session_state.historique[-1]['Profit'], 2)} $" if st.session_state.historique else None)

if st.session_state.historique:
    st.subheader("📈 Progression")
    st.table(st.session_state.historique)
    
    if st.button("Réinitialiser la boule de neige"):
        st.session_state.capital = 100.0
        st.session_state.historique = []
        st.rerun()
