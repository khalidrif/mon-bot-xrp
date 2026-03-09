import streamlit as st
import pandas as pd
import ccxt
import datetime
import time
import plotly.graph_objects as go
from config import get_kraken_connection

# 1. CONFIGURATION PRO 2026
st.set_page_config(page_title="XRP QUANTUM BOT", layout="wide", page_icon="⚡")

# Style CSS pour le look "Terminal de Trading"
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background-color: #1f2630;
        border: 1px solid #31333f;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Connexion via config.py
try:
    kraken = get_kraken_connection()
except Exception as e:
    st.error(f"Erreur de configuration : {e}")
    st.stop()

# --- SIDEBAR : RÉGLAGES DE LA GRILLE ---
with st.sidebar:
    st.header("⚙️ Configuration Grille")
    bot_on = st.toggle("🤖 ACTIVER LE BOT", value=False)
    
    st.divider()
    grid_center = st.number_input("Prix Pivot ($)", value=1.4000, format="%.4f")
    grid_levels = st.slider("Nombre de paliers (Achat & Vente)", 2, 10, 5)
    grid_step = st.number_input("Écart entre paliers ($)", value=0.02, format="%.3f")
    budget_per_step = st.number_input("Budget par palier (USDC)", min_value=25.0, value=30.0)

# --- CORPS DE L'INTERFACE ---
st.title("⚡ XRP Quantum Terminal")

# Zone dynamique pour le rafraîchissement
live_area = st.empty()

while True:
    try:
        # Récupération des données fraîches
        ticker = kraken.fetch_ticker('XRP/USDC')
        prix_actuel = ticker['last']
        balance = kraken.fetch_balance()
        usdc_free = balance.get('free', {}).get('USDC', 0)
        xrp_free = balance.get('free', {}).get('XRP', 0)

        with live_area.container():
            # 1. BARRE DE MÉTRIQUES
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("PORTFOLIO USDC", f"{usdc_free:,.2f} $")
            m2.metric("STOCK XRP", f"{xrp_free:,.2f}")
            m3.metric("PRIX XRP (LAST)", f"{prix_actuel} $", f"{ticker.get('percentage', 0):+.2f}%")
            m4.metric("VALEUR TOTALE", f"{(xrp_free * prix_actuel) + usdc_free:,.2f} $")

            st.divider()

            # 2. GRAPHIQUE + TABLEAU DE LA GRILLE
            col_chart, col_table = st.columns([2, 1])
            
            # Calcul des paliers (Acheter sous le pivot, Vendre au-dessus)
            paliers_vente = [grid_center + (i * grid_step) for i in range(1, grid_levels + 1)]
            paliers_achat = [grid_center - (i * grid_step) for i in range(1, grid_levels + 1)]
            tous_les_paliers = paliers_achat + [grid_center] + paliers_vente

            with col_chart:
                fig = go.Figure()
                
                # --- LIGNE DU PRIX ACTUEL EN BLANC ÉCLATANT ---
                fig.add_hline(
                    y=prix_actuel, 
                    line_dash="dash", 
                    line_color="#FFFFFF", 
                    line_width=3,
                    annotation_text=f" PRIX LIVE: {prix_actuel}$", 
                    annotation_font_color="#FFFFFF"
                )

                # Dessin des lignes de la grille
                for p in tous_les_paliers:
                    color = "#FF4B4B" if p > prix_actuel else "#00FF00"
                    fig.add_hline(y=p, line_width=1, line_color=color, opacity=0.4)
                
                # Réglages visuels Plotly
                fig.update_layout(
                    title="Visualisation de la Grille XRP/USDC",
                    height=450,
                    template="plotly_dark",
                    paper_bgcolor="#0e1117",
                    plot_bgcolor="#0e1117",
                    xaxis=dict(tickfont=dict(color="white")),
                    yaxis=dict(tickfont=dict(color="white")),
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_table:
                st.subheader("📋 Paliers de Trading")
                data_grid = []
                for p in sorted(tous_les_paliers, reverse=True):
                    action = "🔴 VENDRE" if p > prix_actuel else "🟢 ACHETER"
                    if abs(p - grid_center) < 0.0001: action = "⚪ PIVOT"
                    data_grid.append({"Prix": f"{p:.4f} $", "Action": action})
                
                st.table(pd.DataFrame(data_grid))

            # 3. STATUT DU BOT
            if bot_on:
                st.success(f"🤖 BOT EN MARCHE : Surveillance de {len(tous_les_paliers)} niveaux.")
                # Ici on pourrait ajouter la logique d'envoi d'ordres réels
            else:
                st.warning("⏸️ BOT EN PAUSE : Configurez vos paliers et activez le bouton dans la barre latérale.")

            # 4. INVENTAIRE KRAKEN
            with st.expander("🔍 Voir tous mes avoirs détaillés"):
                df_bal = pd.DataFrame(balance['total'].items(), columns=['Actif', 'Quantité'])
                st.dataframe(df_bal[df_bal['Quantité'] > 0], width='stretch')

    except Exception as e:
        st.error(f"Flux interrompu : {e}")

    # Pause de 5 secondes pour le rafraîchissement
    time.sleep(5)

