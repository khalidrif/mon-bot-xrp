import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="XRP Snowball Bot", layout="wide", page_icon="❄️")

# --- INITIALISATION ---
if "paliers" not in st.session_state:
    st.session_state.paliers = []
if "capital_historique" not in st.session_state:
    st.session_state.capital_historique = []

# --- FONCTION DE CALCUL ---
def ajouter_bot(buy, sell, mise):
    st.session_state.paliers.append({
        "buy": buy,
        "sell": sell,
        "mise_initiale": mise,
        "statut": "EN ATTENTE", # EN ATTENTE -> ACHETÉ -> VENDU
        "resultat": 0.0
    })

# --- UI : HEADER ---
st.title("❄️ XRP Snowball Bot")
st.markdown("Chaque profit est réinvesti dans le palier suivant pour maximiser les intérêts composés.")

# --- SIDEBAR : LE MARCHÉ ---
with st.sidebar:
    st.header("📊 Simulation Marché")
    prix_actuel = st.number_input("Prix XRP Actuel ($)", value=1.340, step=0.001, format="%.3f")
    st.divider()
    if st.button("Effacer tout l'historique"):
        st.session_state.paliers = []
        st.rerun()

# --- LOGIQUE DE MISE À JOUR (AUTO) ---
profit_total_realise = 0.0
capital_disponible = 0.0

for p in st.session_state.paliers:
    # 1. Automatisme d'Achat
    if p["statut"] == "EN ATTENTE" and prix_actuel <= p["buy"]:
        p["statut"] = "ACHETÉ"
    
    # 2. Automatisme de Vente
    if p["statut"] == "ACHETÉ" and prix_actuel >= p["sell"]:
        p["statut"] = "VENDU"
        # Calcul du gain : (Prix Vente / Prix Achat) * Mise
        p["resultat"] = (p["sell"] / p["buy"]) * p["mise_initiale"]
    
    # Calcul du profit cumulé pour le dashboard
    if p["statut"] == "VENDU":
        profit_total_realise += (p["resultat"] - p["mise_initiale"])
        capital_disponible = p["resultat"]

# --- UI : DASHBOARD ---
c1, c2, c3 = st.columns(3)
c1.metric("Prix XRP", f"{prix_actuel} $")
c2.metric("Profit Cumulé", f"+{round(profit_total_realise, 4)} $", delta="USDC")
c3.metric("Mise Prochain Bot", f"{round(capital_disponible if capital_disponible > 0 else 10.0, 2)} $")

# --- UI : CONFIGURATION ---
with st.expander("🚀 Lancer un nouveau palier", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    # Suggestion automatique de la mise (Boule de Neige)
    mise_suggeree = capital_disponible if capital_disponible > 0 else 10.0
    
    buy_input = col1.number_input("Cible d'Achat", value=prix_actuel - 0.01, format="%.3f")
    sell_input = col2.number_input("Cible de Vente", value=prix_actuel + 0.02, format="%.3f")
    mise_input = col3.number_input("Capital à engager", value=mise_suggeree)
    
    if st.button("Activer le Palier", use_container_width=True):
        ajouter_bot(buy_input, sell_input, mise_input)
        st.success(f"Bot activé pour {mise_input}$ !")
        st.rerun()

# --- UI : ÉTAT DES BOTS ---
st.subheader("📝 Suivi des opérations")
if not st.session_state.paliers:
    st.info("Aucun palier actif. Configurez votre premier trade ci-dessus.")
else:
    # Transformation en DataFrame pour un affichage propre
    df_bots = []
    for i, p in enumerate(st.session_state.paliers):
        df_bots.append({
            "N°": i + 1,
            "Statut": "⏳ Attend Achat" if p["statut"] == "EN ATTENTE" else "🚀 En Position" if p["statut"] == "ACHETÉ" else "✅ Terminé",
            "Achat à": f"{p['buy']} $",
            "Vente à": f"{p['sell']} $",
            "Mise": f"{round(p['mise_initiale'], 2)} $",
            "Résultat": f"{round(p['resultat'], 2)} $" if p['resultat'] > 0 else "En cours..."
        })
    st.table(df_bots)

# --- GRAPHIQUE DE CROISSANCE ---
if profit_total_realise > 0:
    st.subheader("📈 Croissance du Capital")
    # Simulation simple d'une courbe
    historique_gain = [p["resultat"] for p in st.session_state.paliers if p["statut"] == "VENDU"]
    if historique_gain:
        st.line_chart(historique_gain)
