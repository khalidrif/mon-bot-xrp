import streamlit as st
import pandas as pd

st.set_page_config(page_title="XRP Grid Bot", layout="wide")

st.title("🤖 XRP Trading Bot Pro")

# --- Initialisation ---
if "paliers" not in st.session_state:
    st.session_state.paliers = []

# --- Sidebar : Paramètres de simulation ---
with st.sidebar:
    st.header("⚙️ Simulation")
    prix_actuel = st.number_input("Prix XRP Actuel ($)", value=1.3400, format="%.4f", step=0.0001)
    st.info("Simulez la variation du prix pour voir les bots s'activer.")

# --- Ajouter un Bot ---
with st.expander("➕ Configurer un nouveau palier", expanded=True):
    c1, c2, c3 = st.columns(3)
    buy_target = c1.number_input("Cible d'achat (BUY)", value=prix_actuel - 0.01, format="%.4f")
    sell_target = c2.number_input("Cible de vente (SELL)", value=prix_actuel + 0.02, format="%.4f")
    montant_usdc = c3.number_input("Investissement (USDC)", value=10.0, step=1.0)
    
    if st.button("Lancer le Bot sur ce palier", use_container_width=True):
        st.session_state.paliers.append({
            "buy": buy_target,
            "sell": sell_target,
            "usdc": montant_usdc,
            "status": "ATTENTE", # ATTENTE, ACHETÉ, TERMINÉ
            "id": len(st.session_state.paliers)
        })
        st.rerun()

# --- Logique de mise à jour automatique ---
profit_realise = 0.0
for p in st.session_state.paliers:
    # 1. Si prix baisse sous BUY -> Le bot achète
    if p["status"] == "ATTENTE" and prix_actuel <= p["buy"]:
        p["status"] = "ACHETÉ"
    
    # 2. Si prix monte au-dessus de SELL après achat -> Le bot vend
    if p["status"] == "ACHETÉ" and prix_actuel >= p["sell"]:
        p["status"] = "TERMINÉ"
    
    # Calcul du profit réalisé
    if p["status"] == "TERMINÉ":
        profit_realise += (p["sell"] - p["buy"]) * (p["usdc"] / p["buy"])

# --- Affichage des performances ---
m1, m2 = st.columns(2)
m1.metric("Prix XRP", f"{prix_actuel}$")
m2.metric("Profit Réalisé", f"{round(profit_realise, 4)} USDC", delta=f"{round(profit_realise, 2)} $")

# --- Liste des Bots ---
st.subheader("📊 État des paliers")
if not st.session_state.paliers:
    st.write("Aucun bot actif.")
else:
    for i, p in enumerate(st.session_state.paliers):
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
        
        col1.write(f"**Bot {i+1}**")
        
        # Style selon le statut
        if p["status"] == "ATTENTE":
            col2.warning(f"⏳ Cible: {p['buy']}")
        elif p["status"] == "ACHETÉ":
            col2.success(f"🎯 Acheté à: {p['buy']}")
        else:
            col2.info(f"✅ Terminé")

        col3.error(f"🔴 Vente: {p['sell']}")
        col4.write(f"💰 {p['usdc']} USDC")
        
        if col5.button("🗑️", key=f"del_{i}"):
            st.session_state.paliers.pop(i)
            st.rerun()

# --- Option : Nettoyer les terminés ---
if any(p["status"] == "TERMINÉ" for p in st.session_state.paliers):
    if st.button("Nettoyer les bots terminés"):
        st.session_state.paliers = [p for p in st.session_state.paliers if p["status"] != "TERMINÉ"]
        st.rerun()
